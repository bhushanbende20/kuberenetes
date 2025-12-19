from pyflink.datastream import StreamExecutionEnvironment
from pyflink.common.typeinfo import Types

# Setup environment
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(4)

# Sample data
data = ["hello flink", "hello pyflink", "flink on kubernetes"]

ds = env.from_collection(data, type_info=Types.STRING())

# Word count
(
    ds.flat_map(lambda x: x.split(), output_type=Types.STRING())
      .map(lambda x: (x, 1), output_type=Types.TUPLE([Types.STRING(), Types.INT()]))
      .key_by(lambda x: x[0])
      .sum(1)
      .print()
)

env.execute("pyflink-wordcount")
