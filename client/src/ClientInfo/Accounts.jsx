import { useState, useEffect } from "react";
import LoadingAnimation from "../Components/LoadingAnimation";
import ErrorAlert from "../Components/ErrorAlert";

function Accounts({ client_id, password }) {
    const apiUrl = "http://127.0.0.1:8000/account/";
    const [productsLoading, setProductsLoading] = useState(true);
    const [accountsLoading, setAccountsLoading] = useState(true);
    const [fetchError, setFetchError] = useState(null);

    const [accounts, setAccounts] = useState([]);
    const [products, setProducts] = useState([]);

    async function getAccounts() {
        try {
            const response = await fetch(apiUrl + "account_list_for_client/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    client_id: client_id,
                    password: password,
                }),
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || response.statusText);
            }
            const data = await response.json();
            setAccounts(data);
        } catch (error) {
            throw new Error(error.message);
        } finally {
            setAccountsLoading(false); // Set loading to false once done
        }
    }

    async function getProducts() {
        try {
            const response = await fetch(apiUrl + "get_product_list/", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || response.statusText);
            }
            const data = await response.json();
            setProducts(data);
        } catch (error) {
            throw new Error(error.message);
        } finally {
            setProductsLoading(false); // Set loading to false once done
        }
    }

    useEffect(() => {
        try {
            getAccounts();
            getProducts();
        } catch (error) {
            setFetchError(error.message);
        }
    }, []); // Empty dependency array to run only once when the component mounts

    if (productsLoading || accountsLoading) {
        return <LoadingAnimation />; // Show loading message while data is being fetched
    }

    if (fetchError) {
        return <ErrorAlert error={fetchError} />; // Display any error that occurs
    }

    return (
        <div className="flex flex-col w-1/3 space-y-6">
            {products.map((product) => (
                <details className="flex flex-col space-y-6 bg-neutral-50 p-4 rounded-xl shadow-md">
                    <summary className="flex space-x-6">
                        <img src="down-arrow.svg" alt="Drop Down Arrow" />
                        <h2 className="font-bold text-xl text-center">
                            {product.product_name} Accounts
                        </h2>
                    </summary>
                    <ol className="flex flex-col space-y-6">
                        {accounts
                            .filter(
                                (account) =>
                                    account.product_id === product.product_id
                            )
                            .map((account) => (
                                <li key={account.account_id}>
                                    <div>
                                        <div>
                                            <span className="font-bold">
                                                Account ID:
                                            </span>{" "}
                                            {account.account_id}
                                        </div>
                                        <div>
                                            <span className="font-bold">
                                                Balance:
                                            </span>{" "}
                                            ${account.balance}
                                        </div>
                                    </div>
                                </li>
                            ))}
                    </ol>
                </details>
            ))}
        </div>
    );
}

export default Accounts;
