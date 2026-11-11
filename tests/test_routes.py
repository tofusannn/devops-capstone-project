"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...

    
    def test_read_an_account(self):
        """It should Read a single Account"""

        # 1. Create test account
        account = AccountFactory()

        # 2. Send POST request to create an account
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )

        # 3. Check that the account was created
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        # 4. Get the newly created account data and ID
        new_account = response.get_json()
        account_id = new_account["id"]

        # 5. Send GET request using the created ID
        response = self.client.get(
            f"{BASE_URL}/{account_id}"
        )

        # 6. Check HTTP status code
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # 7. Verify the returned account data
        data = response.get_json()
        self.assertEqual(data, new_account)


    def test_account_not_found(self):
        """It should return 404 when Account is not found"""

        # Send GET request with nonexistent account ID
        response = self.client.get(f"{BASE_URL}/0")

        # Verify HTTP 404 Not Found
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )

    def test_method_not_allowed(self):
        """It should return 405 for unsupported HTTP method"""
        response = self.client.put("/health")

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_list_all_accounts(self):
        """It should List all Accounts"""
        accounts = self._create_accounts(3)

        response = self.client.get(BASE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), len(accounts))
        for account in accounts:
            self.assertIn(account.serialize(), data)

    def test_list_accounts_empty(self):
        """It should return an empty list when no Accounts exist"""
        response = self.client.get(BASE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])
    def test_update_an_account(self):
        """It should Update an existing Account and persist changes"""
        account = self._create_accounts(1)[0]
        updated_data = account.serialize()
        updated_data["name"] = "Updated Customer Name"
        updated_data["email"] = "updated@example.com"
        updated_data["address"] = "123 Updated Street"

        response = self.client.put(
            f"{BASE_URL}/{account.id}", json=updated_data
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), updated_data)

        read_response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.get_json(), updated_data)

    def test_update_account_not_found(self):
        """It should return 404 when the Account does not exist"""
        account_data = AccountFactory().serialize()
        response = self.client.put(f"{BASE_URL}/0", json=account_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_account_invalid_data(self):
        """It should reject updates with missing required fields"""
        account = self._create_accounts(1)[0]
        response = self.client.put(
            f"{BASE_URL}/{account.id}", json={"name": "Incomplete"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_account_unsupported_media_type(self):
        """It should reject updates without JSON content type"""
        account = self._create_accounts(1)[0]
        response = self.client.put(
            f"{BASE_URL}/{account.id}",
            data="not json",
            content_type="text/plain"
        )
        self.assertEqual(
            response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    def test_delete_an_account(self):
        """It should Delete an existing Account"""
        account = self._create_accounts(1)[0]

        response = self.client.delete(f"{BASE_URL}/{account.id}")

        self.assertEqual(
            response.status_code, status.HTTP_204_NO_CONTENT
        )
        self.assertEqual(response.data, b"")

        read_response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(
            read_response.status_code, status.HTTP_404_NOT_FOUND
        )

    def test_delete_account_not_found(self):
        """It should return 404 when the Account does not exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )
