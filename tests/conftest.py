import os
import pytest
from json import loads as load_json
from saraki import Saraki
from saraki.model import database, AppUser
from common import Person, Product, Order, OrderLine, TransactionManager


needdatabase = pytest.mark.skipif(
    os.getenv('DATABASE_URI') is None,
    reason="This need a database connection and DATABASE_URI is not defined"
)


@pytest.fixture(scope='session')
def _setup_database(request):
    """Setup the database

    Creates all tables on setup and deletes all tables on cleanup.
    """

    _app = Saraki(__name__, db=None)
    _app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['TEST_DATABASE_URI']
    database.init_app(_app)

    with _app.app_context():
        database.create_all()

    def teardown():
        with _app.app_context():
            database.session.remove()
            database.drop_all()

    request.addfinalizer(teardown)

    return database


@pytest.fixture(scope='session')
def _insert_data(_setup_database):
    """Put the database in a known state by inserting
    predefined data.

    This is a session scoped fixture.
    """

    _app = Saraki(__name__, db=None)
    _app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['TEST_DATABASE_URI']
    database.init_app(_app)

    with open('tests/data/product.json', 'r') as products_file, \
            open('tests/data/order.json', 'r') as orders_file, \
            open('tests/data/order_line.json', 'r') as order_lines_file,  \
            open('tests/data/person.json', 'r') as persons_file, \
            open('tests/data/user.json') as users_file:

        person_ls = load_json(persons_file.read())
        product_ls = load_json(products_file.read())
        order_ls = load_json(orders_file.read())
        order_line_ls = load_json(order_lines_file.read())
        user_ls = load_json(users_file.read())

    with _app.app_context():
        database.session.add_all([Person(**item) for item in person_ls])
        database.session.add_all([Product(**item) for item in product_ls])
        database.session.add_all([Order(**item) for item in order_ls])
        database.session.add_all([OrderLine(**item) for item in order_line_ls])

        for u in user_ls:

            data = {
                'username': u['username'],
                'canonical_username': u['username'].lower(),
                'password': u['hashed_password'],
                'email': u['email']
            }

            user = AppUser(**data)
            database.session.add(user)

        database.session.commit()


@pytest.fixture
def data(_insert_data, database_conn):
    pass


@pytest.fixture(scope='session')
def _trn():
    """Create a session wide instance of TransactionManager class.

    TransactionManager helps create nested database transactions.
    This help rollback any transaction using PostgreSQL savepoints.
    """
    return TransactionManager(database)


@pytest.fixture
def app(request):

    app = Saraki('flask_test', root_path=os.path.dirname(__file__), db=None)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'secret'

    return app


@pytest.fixture
def request_ctx(app):
    return app.test_request_context


@pytest.fixture
def database_conn(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TEST_DATABASE_URI')
    database.init_app(app)


@pytest.fixture
def savepoint(_setup_database, database_conn, _trn, request):
    _trn.start()

    def teardown():
        _trn.close()

    request.addfinalizer(teardown)


@pytest.fixture
def ctx(app, request):
    """Push a new application context and closes it automatically
    when the test goes out of scope.

    This helps to avoid creating application contexts manually
    either by calling app.app_context() with python `with` statement or
    by pushing or popping manually.
    """
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)

    return ctx


@pytest.fixture
def client(app, ctx, savepoint, database_conn):
    """Flask Test Client

    This starts a database nested transaction and then closes it
    when the test goes out of scope in order to rollback any change
    made to the database.
    """

    return app.test_client()


@pytest.fixture
def xclient(app):
    """Flask Test Client (No DB transaction)"""

    return app.test_client()
