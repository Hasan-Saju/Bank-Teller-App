import Clients from "./Clients";
import Transactions from "./Transactions";
import TellerHub from "./TellerHub";
import NetFlow from "./NetFlow";
import TransactionCounts from "./TransactionCounts";

function Dashboard() {
    return (
        <div className="flex justify-between h-full p-4">
            <div className="flex flex-col space-y-6 w-1/4">
                <NetFlow />
                <TransactionCounts />
            </div>
            <TellerHub />
            <div className="flex flex-col space-y-6 w-1/4">
                <Clients />
                <Transactions />
            </div>
        </div>
    );
}

export default Dashboard;
