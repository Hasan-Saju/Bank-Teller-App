from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.contrib.auth.hashers import check_password
from django.db.models import Sum  # Import the Sum function

import json
import random
from .serializers import ClientSerializer, AccountSerializer, BranchSerializer, ProductSerializer, CreateClientSerializer, TransactionSerializer, TellerSerializer
from .models import Client, Account, Branch, Product, Transaction, Teller, Schedule

# For ml model
from datetime import datetime
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# Create your views here.

@csrf_exempt
def get_branch_list(request):
    branches = Branch.objects.all()
    serializer = BranchSerializer(branches, many=True)
    return JsonResponse(serializer.data, safe=False)
@csrf_exempt
def get_product_list(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return JsonResponse(serializer.data, safe=False)

@csrf_exempt
def create_new_client(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = CreateClientSerializer(data=data)
        if serializer.is_valid():
            # Generate a unique 10-digit client_id
            while True:
                client_id = str(random.randint(1000000000, 9999999999))
                if not Client.objects.filter(client_id=client_id).exists():
                    break
            serializer.save(client_id=client_id)
            response_data = {
            'client_id': client_id
        }
            return JsonResponse(response_data, status=201)
        return JsonResponse(serializer.errors, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def get_client_details(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        client_id = data.get('client_id')
        password = data.get('password')

        try:
            client = Client.objects.get(client_id=client_id, password=password)
        except Client.DoesNotExist:
            return JsonResponse({'error': 'Invalid client_id or password'}, status=400)

        serializer = ClientSerializer(client)
        response_data = serializer.data
        # response_data.pop('password', None)  # Remove the password field from the response
        return JsonResponse(response_data, safe=False, status=200)


    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def create_new_account(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        client_id = data.get('client_id')
        product_id = data.get('product_id')

        # Check if the client and product exist
        try:
            client = Client.objects.get(client_id=client_id)
            product = Product.objects.get(product_id=product_id)
        except (Client.DoesNotExist, Product.DoesNotExist):
            return JsonResponse({'error': 'Invalid client_id or product_id'}, status=400)
        # Generate a unique 9-digit account_id
        while True:
            account_id = str(random.randint(100000000, 999999999))
            if not Account.objects.filter(account_id=account_id).exists():
                break

        # Create a new Account object
        account = Account(
            account_id=account_id,
            client_id=client,
            product_id=product,
            balance=0
        )

        # Save the Account object to the database
        account.save()

        # Prepare the JSON response
        response_data = AccountSerializer(account).data

        return JsonResponse(response_data, status=201)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def get_account_list_for_a_client(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        client_id = data.get('client_id')
        password = data.get('password')

        try:
            client = Client.objects.get(client_id=client_id, password=password)
        except Client.DoesNotExist:
            return JsonResponse({'error': 'Invalid client_id or password'}, status=400)

        accounts = Account.objects.filter(client_id=client)
        serializer = AccountSerializer(accounts, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Helper function to fetch historical transaction data
def fetch_historical_data():
    """
    Fetch historical transaction data from the database.
    """
    transactions = Transaction.objects.all().values(
        'amount',
        'timestamp',
        'from_account_id__balance',
        'transaction_type',
        'from_account_id__product_id__product_name'  # Assuming account type is derived from product name
    )
    df = pd.DataFrame(transactions)
    if df.empty:
        raise ValueError("No transaction data found in the database.")

    # Rename columns for clarity
    df.rename(columns={
        'amount': 'amount',
        'timestamp': 'timestamp',
        'from_account_id__balance': 'balance',
        'transaction_type': 'transaction_type',
        'from_account_id__product_id__product_name': 'account_type'
    }, inplace=True)

    # Convert timestamp to hour for time-based patterns
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour

    # Encode categorical features (transaction_type and account_type)
    label_encoders = {
        'transaction_type': LabelEncoder(),
        'account_type': LabelEncoder()
    }
    for column, encoder in label_encoders.items():
        df[column] = encoder.fit_transform(df[column])

    return df[['amount', 'hour', 'balance', 'transaction_type', 'account_type']]


# Helper function to train the Isolation Forest model
def train_model(data):
    """
    Train the Isolation Forest model using the provided data.
    """
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    model.fit(data)
    return model

@csrf_exempt
def create_transaction(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        from_account_id = data.get('from_account_id')
        to_account_id = data.get('to_account_id')
        amount = data.get('amount')
        timestamp = data.get('timestamp')
        transaction_type = 'Transfer'

        # Check if the accounts exist
        try:
            from_account = Account.objects.get(account_id=from_account_id)
            to_account = Account.objects.get(account_id=to_account_id)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Invalid from_account_id or to_account_id'}, status=400)

        # Check if the from_account has sufficient balance
        if from_account.balance < amount:
            return JsonResponse({'error': 'Insufficient balance in your account to complete the transaction'}, status=400)

        # Generate a unique 10-digit transaction_id
        while True:
            transaction_id = str(random.randint(1000000000, 9999999999))
            if not Transaction.objects.filter(transaction_id=transaction_id).exists():
                break

        # Deduct the amount from from_account and add to to_account
        from_account.balance -= amount
        to_account.balance += amount

        # Save the updated account balances
        from_account.save()
        to_account.save()

        # Create a new Transaction object
        transaction = Transaction(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            from_account_id=from_account,
            to_account_id=to_account,
            amount=amount,
            timestamp=timestamp
        )

        # Save the Transaction object to the database
        transaction.save()

        ''' Fraud detection
        try:
            historical_data = fetch_historical_data()
            model = train_model(historical_data)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)

        # Prepare data for fraud detection
        transaction_data = {
            'amount': [amount],
            'hour': [datetime.now().hour],
            'balance': [from_account.balance],
            'transaction_type': [LabelEncoder().fit(historical_data['transaction_type']).transform([transaction_type])[0]],
            'account_type': [LabelEncoder().fit(historical_data['account_type']).transform(
                [from_account.product_id.product_name])[0]]
        }
        df = pd.DataFrame(transaction_data)
        prediction = model.predict(df)
        is_fraud = prediction[0] == -1
        '''

        # Return a JSON response with the updated balance, fraud flag and transaction details
        response_data = TransactionSerializer(transaction).data
        response_data['updated_balance'] = from_account.balance
        # response_data['fraud'] = is_fraud
        return JsonResponse(response_data, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def get_all_transactions(request):
    if request.method == 'GET':
        try:
            transactions = Transaction.objects.all()
            serializer = TransactionSerializer(transactions, many=True)
            return JsonResponse(serializer.data, safe=False, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

def calculate_balance_after_transaction(current_balance, amount, transaction_type):
    if transaction_type=='credit':
        return current_balance + amount
    elif transaction_type=='debit':
        return current_balance - amount
 
@csrf_exempt
def depositMoney(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # clientId = data.get('client_id')
        account_id = data.get('account_no')
        amount = data.get('amount')
        timestamp = data.get('timestamp')

        # Check if the account exists
        try:
            account = Account.objects.get(account_id=account_id)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account does not exist'}, status=404)

        # Add the amount to the account balance
        account.balance = calculate_balance_after_transaction(current_balance=account.balance, amount=amount,
                                                              transaction_type='credit')

        # Save the updated account balance
        account.save()
         
         # Generate a unique transaction_id
        while True:
            transaction_id = str(random.randint(1000000000, 9999999999))
            if not Transaction.objects.filter(transaction_id=transaction_id).exists():
                break

        transaction = Transaction(
            transaction_id=transaction_id,
            transaction_type='Deposit',
            to_account_id=account,
            amount=amount,
            timestamp=timestamp
        )
        # Save the Transaction object to the database
        transaction.save()

        # Return a JSON response with the updated balance and transaction details
        response_data = TransactionSerializer(transaction).data
        response_data['updated_balance'] = account.balance
        return JsonResponse(response_data, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def withdrawMoney(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # clientId = data.get('client_id')
        account_id = data.get('account_no')
        amount = data.get('amount')
        timestamp = data.get('timestamp')

        # Check if the account exists
        try:
            account = Account.objects.get(account_id=account_id)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Account does not exist'}, status=404)

        # Check if the account has sufficient balance
        if account.balance < amount:
            return JsonResponse({'error': 'Insufficient balance'}, status=400)

        # Deduct the amount from the account balance
        account.balance = calculate_balance_after_transaction(current_balance=account.balance, amount=amount,
                                                              transaction_type='debit')

        # Save the updated account balance
        account.save()
         # Generate a unique transaction_id
        while True:
            transaction_id = str(random.randint(1000000000, 9999999999))
            if not Transaction.objects.filter(transaction_id=transaction_id).exists():
                break

        transaction = Transaction(
            transaction_id=transaction_id,
            transaction_type='Withdraw',
            from_account_id=account,
            amount=amount,
            timestamp=timestamp
        )
        # Save the Transaction object to the database
        transaction.save()

        # Return a JSON response with the updated balance and transaction details
        response_data = TransactionSerializer(transaction).data
        response_data['updated_balance'] = account.balance
        return JsonResponse(response_data, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def employee_login(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        employee_id = data.get('employee_id')
        password = data.get('password')

        try:
            teller = Teller.objects.get(employee_id=employee_id)
        except Teller.DoesNotExist:
            return JsonResponse({'error': 'Invalid employee_id or password'}, status=400)

        # Validate the password
        if teller.check_password(password):
            return JsonResponse({'message': 'Login successful', 'employee_id': teller.employee_id, 'first_name': teller.first_name}, status=200)
        else:
            return JsonResponse({'error': 'Invalid email or password'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def create_teller(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        
        # Generate a unique employee_id
        while True:
            employee_id = str(random.randint(100000, 999999))
            if not Teller.objects.filter(employee_id=employee_id).exists():
                break
        
        data['employee_id'] = employee_id  # Add the generated employee_id to the data

        serializer = TellerSerializer(data=data)
        if serializer.is_valid():
            teller = serializer.save()  # The password will be hashed automatically by the model
            response_data = serializer.data
            response_data.pop('password', None)  # Remove the password field from the response
            return JsonResponse(response_data, status=201)
        
        return JsonResponse(serializer.errors, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def transactionList(request):
    if request.method == 'GET':
        transactions = Transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
@csrf_exempt
def tellerList(request):
    if request.method == 'GET':
        tellers = Teller.objects.all()
        serializer = TellerSerializer(tellers, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    

@csrf_exempt
def transactionListforAccount(request):
    if request.method == 'POST':
        data = JSONParser().parse(request)
        account_id = data.get('account_id')
        try:
            account = Account.objects.get(account_id=account_id)
        except Account.DoesNotExist:
            return JsonResponse({'error': 'Invalid account_id'}, status=400)
        
        from_transactions = Transaction.objects.filter(from_account_id=account)
        to_transactions = Transaction.objects.filter(to_account_id=account)
        
        from_transactions_serializer = TransactionSerializer(from_transactions, many=True)
        to_transactions_serializer = TransactionSerializer(to_transactions, many=True)
        return JsonResponse({'debit': from_transactions_serializer.data, 'credit': to_transactions_serializer.data}, safe=False, status=200)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def transaction_summary(request):
    if request.method == 'GET':
        total_transactions_count = Transaction.objects.count()
        total_deposits_count = Transaction.objects.filter(transaction_type='Deposit').count()
        total_withdrawals_count = Transaction.objects.filter(transaction_type='Withdraw').count()
        total_transfer_count = Transaction.objects.filter(transaction_type='Transfer').count()

        total_withdrawals_amount = Transaction.objects.filter(transaction_type='Withdraw').aggregate(Sum('amount'))['amount__sum']
        total_deposits_amount = Transaction.objects.filter(transaction_type='Deposit').aggregate(Sum('amount'))['amount__sum']
        
         # Handle cases where there are no transactions
        if total_withdrawals_amount is None:
            total_withdrawals_amount = 0.00
        if total_deposits_amount is None:
            total_deposits_amount = 0.00
                
        return JsonResponse({
            'total_transactions_count': total_transactions_count,
            'total_deposits_count': total_deposits_count,
            'total_withdrawals_count': total_withdrawals_count,
            'total_transfer_count': total_transfer_count,
            'total_withdrawals_amount': total_withdrawals_amount,
            'total_deposits_amount': total_deposits_amount,
            'net_cash_flow': total_deposits_amount - total_withdrawals_amount
        }, status=200)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)