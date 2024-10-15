from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import WalletTransactions, WithdrawingRequests
from api.models import CustomUser
from schedule.models import PaymentDetails


class WalletTransactionsModelTest(TestCase):
    """Test case for WalletTransactions model."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser@example.com',
            password='testpassword'
        )
        self.payment_details = PaymentDetails.objects.create(
            payment_method='upi', transaction_id='test123', payment_for='test'
        )
        self.wallet_transaction = WalletTransactions.objects.create(
            user=self.user,
            payment_details=self.payment_details,
            wallet_balance=100.00,
            amount=50.00,
            transaction_type='credit'
        )

    def test_wallet_transaction_str(self):
        """Test the string representation of WalletTransactions."""
        self.assertEqual(
            str(self.wallet_transaction),
            f"Credit of 50.00 on {self.wallet_transaction.created_at}"
        )


class WithdrawingRequestsModelTest(TestCase):
    """Test case for WithdrawingRequests model."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser@example.com',
            password='testpassword'
        )
        self.wallet_transaction = WalletTransactions.objects.create(
            user=self.user,
            wallet_balance=100.00,
            amount=50.00,
            transaction_type='debit'
        )
        self.withdrawal_request = WithdrawingRequests.objects.create(
            user=self.user,
            amount=50.00,
            status='pending',
            upi_id='test@upi',
            payment_obj=self.wallet_transaction
        )

    def test_withdrawing_request_str(self):
        """Test the string representation of WithdrawingRequests."""
        self.assertEqual(
            str(self.withdrawal_request),
            f"Withdrawal Request for {self.user.username} of 50.00"
        )


class WalletViewTests(TestCase):
    """Test cases for Wallet-related API views."""

    def setUp(self):
        self.client = APIClient()

        # Create a user
        self.user = CustomUser.objects.create_user(
            username='testuser@example.com',
            password='testpassword'
        )

        # Obtain JWT token
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser@example.com',
            'password': 'testpassword'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Set the token in the Authorization header
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_add_funds(self):
        """Test the add funds endpoint."""
        response = self.client.post(reverse('add-funds'), {'amount': 100})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_balance(self):
        """Test the get balance endpoint."""
        WalletTransactions.objects.create(
            user=self.user,
            wallet_balance=100.00,
            amount=100.00,
            transaction_type='credit'
        )
        response = self.client.get(reverse('get-wallet-balance'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['balance'], 100.00)

    def test_withdraw_funds(self):
        """Test the withdraw funds endpoint."""
        WalletTransactions.objects.create(
            user=self.user,
            wallet_balance=100.00,
            amount=100.00,
            transaction_type='credit'
        )
        response = self.client.post(
            reverse('withdraw-money'), {'amount': 50, 'upi_id': 'test@upi'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class WithdrawRequestsViewSetTests(TestCase):
    """Test cases for withdrawing requests view set."""

    def setUp(self):
        self.client = APIClient()

        # Create a user
        self.user = CustomUser.objects.create_user(
            username='testuser@example.com',
            password='testpassword'
        )

        # Obtain JWT token
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser@example.com',
            'password': 'testpassword'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Set the token in the Authorization header
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_withdrawing_request(self):
        """Test creating a withdrawing request."""

        # Create a wallet transaction to simulate existing wallet balance
        wallet_transaction = WalletTransactions.objects.create(
            user=self.user,
            wallet_balance=100.00,
            amount=100.00,
            transaction_type='credit'
        )

        # Make the withdrawal request with user and payment_obj fields
        response = self.client.post(reverse('withdrawal-requests-list'), {
            'amount': 50,
            'upi_id': 'test@upi',
            'user': self.user.id,
            'payment_obj': wallet_transaction.id
        })

        print(response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
