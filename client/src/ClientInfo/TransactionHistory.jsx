import React, { useState, useEffect } from "react";
import LoadingSpinner from "../Components/LoadingSpinner";
import ErrorAlert from "../Components/ErrorAlert";

function TransactionHistory({ account_id, product_name, close }) {
    const apiUrl = "http://127.0.0.1:8000/account/";
    const [loading, setLoading] = useState(true);
    const [fetchError, setFetchError] = useState(null);

    const [debitList, setDebitList] = useState([]);
    const [creditList, setCreditList] = useState([]);
    const [showDebit, setShowDebit] = useState(true); // State to toggle between tables

    async function getData() {
        try {
            const response = await fetch(
                apiUrl + "transactionListforAccount/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ account_id }),
                }
            );
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || response.statusText);
            }
            const data = await response.json();
            setDebitList(data.debit);
            setCreditList(data.credit);
        } catch (error) {
            throw new Error(error.message);
        } finally {
            setLoading(false); // Set loading to false once done
        }
    }

    useEffect(() => {
        const fetchData = async () => {
            try {
                await getData();
            } catch (error) {
                setFetchError(error.message);
            }
        };
        fetchData();
    }, []); // Run only once when the component mounts

    if (loading) {
        return <LoadingSpinner />; // Show loading message while data is being fetched
    }

    return (
        <div className="bg-neutral-50 p-6 rounded-xl w-3/5 min-w-fit shadow-md space-y-5">
            <img
                src="back.svg"
                alt="Back"
                className="w-6 cursor-pointer"
                onClick={close}
            />
            <h2 className="font-bold text-xl text-center">
                Account: {account_id} - {product_name}
            </h2>

            {fetchError && <ErrorAlert message={fetchError} />}

            {!fetchError && (
                <div className="space-y-5">
                    <div className="flex justify-center space-x-4">
                        <button
                            className={`p-2 w-fit rounded-md text-white ${
                                showDebit ? "bg-gray-400" : "bg-blue-500"
                            }`}
                            onClick={() => setShowDebit(true)}
                        >
                            Show Debit
                        </button>
                        <button
                            className={`p-2 w-fit rounded-md text-white ${
                                !showDebit ? "bg-gray-400" : "bg-blue-500"
                            }`}
                            onClick={() => setShowDebit(false)}
                        >
                            Show Credit
                        </button>
                    </div>

                    {showDebit && (
                        <div className="space-y-5">
                            <h3 className="font-semibold text-lg">
                                Debit Transactions
                            </h3>
                            {debitList.length > 0 ? (
                                <table className="w-full">
                                    <thead>
                                        <tr className="bg-gray-200">
                                            <th className="border border-gray-300 px-4 py-2">
                                                ID
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Type
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                To
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Amount
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Date
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Time
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {debitList.map((transaction) => {
                                            const date = transaction.timestamp
                                                ? new Date(
                                                      transaction.timestamp
                                                  )
                                                : null;
                                            const formattedDate = date
                                                ? date.toLocaleDateString()
                                                : "N/A";
                                            const formattedTime = date
                                                ? date.toLocaleTimeString()
                                                : "N/A";

                                            return (
                                                <tr
                                                    key={
                                                        transaction.transaction_id ||
                                                        Math.random()
                                                    }
                                                    className="hover:bg-gray-100"
                                                >
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.transaction_id ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.transaction_type ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.to_account_id ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.amount ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {formattedDate}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {formattedTime}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            ) : (
                                <p className="text-center">
                                    No debit transactions found
                                </p>
                            )}
                        </div>
                    )}

                    {!showDebit && (
                        <div className="space-y-5">
                            <h3 className="font-semibold text-lg">
                                Credit Transactions
                            </h3>
                            {creditList.length > 0 ? (
                                <table className="w-full">
                                    <thead>
                                        <tr className="bg-gray-200">
                                            <th className="border border-gray-300 px-4 py-2">
                                                ID
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Type
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                From
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Amount
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Date
                                            </th>
                                            <th className="border border-gray-300 px-4 py-2">
                                                Time
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {creditList.map((transaction) => {
                                            const date = transaction.timestamp
                                                ? new Date(
                                                      transaction.timestamp
                                                  )
                                                : null;
                                            const formattedDate = date
                                                ? date.toLocaleDateString()
                                                : "N/A";
                                            const formattedTime = date
                                                ? date.toLocaleTimeString()
                                                : "N/A";

                                            return (
                                                <tr
                                                    key={
                                                        transaction.transaction_id ||
                                                        Math.random()
                                                    }
                                                    className="hover:bg-gray-100"
                                                >
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.transaction_id ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.transaction_type ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.from_account_id ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {transaction.amount ||
                                                            "N/A"}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {formattedDate}
                                                    </td>
                                                    <td className="border border-gray-300 px-4 py-2">
                                                        {formattedTime}
                                                    </td>
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            ) : (
                                <p className="text-center">
                                    No credit transactions found
                                </p>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default TransactionHistory;
