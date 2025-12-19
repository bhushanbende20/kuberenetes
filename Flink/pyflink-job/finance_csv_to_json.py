import csv
import json

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.typeinfo import Types


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    input_path = "/opt/flink/data/Finance_data.csv"

    # Read CSV as text
    text_stream = env.read_text_file(input_path)

    # Skip header
    data_stream = text_stream.filter(lambda l: not l.startswith("gender"))

    headers = [
        "gender", "age", "Investment_Avenues", "Mutual_Funds",
        "Equity_Market", "Debentures", "Government_Bonds",
        "Fixed_Deposits", "PPF", "Gold", "Stock_Marktet",
        "Factor", "Objective", "Purpose", "Duration",
        "Invest_Monitor", "Expect", "Avenue",
        "Savings_Objectives", "Reason_Equity",
        "Reason_Mutual", "Reason_Bonds",
        "Reason_FD", "Source"
    ]

    def csv_to_json(line):
        values = next(csv.reader([line]))
        record = dict(zip(headers, values))
        return json.dumps(record)

    json_stream = data_stream.map(
        csv_to_json,
        output_type=Types.STRING()
    )

    # ✅ PRINT ONLY (goes to TaskManager logs)
    json_stream.print()

    env.execute("finance-csv-to-json-print-only")


if __name__ == "__main__":
    main()
