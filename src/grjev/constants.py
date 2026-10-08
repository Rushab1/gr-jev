"""Every constant in the project: paths, URLs, hashes, model names, seeds and thresholds."""

from fractions import Fraction
from pathlib import Path

# The package is installed in editable mode, so this file sits in <repo>/src/grjev/.
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RESULTS_DIR = REPO_ROOT / "results"

HTTP_TIMEOUT_SECONDS = 60.0
GITHUB_RAW_URL = "https://raw.githubusercontent.com"
HUGGINGFACE_URL = "https://huggingface.co"

JEV_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-1.13.0"
JEV_KEY_ENV = "TYPESAFE_API_KEY"
JEV_MAX_OPTIONS = 255
# Rate limited, unavailable and overloaded. TypeSafe asks for a retry with backoff on these.
JEV_RETRY_STATUSES = (429, 503, 529)
JEV_MAX_ATTEMPTS = 5
JEV_BACKOFF_SECONDS = 2.0
JEV_CACHE_DIR = DATA_DIR / "cache" / "jev"
# Rushab's limit on the number of Jev calls. A run that would pass it does not start. Raise it only on his instruction.
# Raised from 100 to 360 on 2026-10-05 for the first subset, to 651 on 2026-10-06 for the 300 calls of the wording
# subset on StableToolBench, to 710 the same day for the 59 calls of the growth subset of 50 queries, and to 760 the
# same day for the 50 calls of the reworded subset of the same 50 queries. Raised to 1,110 on 2026-10-06 for a second
# run of the 300 requests of the wording subset and for 50 calls of the reworded subset with only the rewordings listed.
# Raised to 1,160 on 2026-10-07 for 50 calls of the reworded subset with the rewordings in a seeded order, and to
# 1,210 the same day for the 50 calls of the rotated subset. Raised to 1,510 on 2026-10-07 for MetaTool: a second run of
# the 250 requests of the position subset, and the 50 calls of the rotated subset. Raised to 1,511 the same day for one
# request that lists one API five times, and to 1,512 for a second such request. Raised to 1,612 the same day for the
# copied subsets of MetaTool and StableToolBench, 50 calls each, and to 1,662 for the 50 calls of the absent subset of
# MetaTool, to 1,712 for the 50 calls of its absent_random subset, and to 1,762 for the 50 calls of its unrelated
# subset. Raised to 1,962 on 2026-10-08 for four subsets of MMLU with 50 calls each: own, copied, unrelated and
# absent_random.
JEV_CALL_LIMIT = 1962
# Requests sent to Jev at the same time. TypeSafe allows 80 requests per second.
JEV_WORKERS = 8
JEV_DOLLARS_PER_MILLION_INPUT_TOKENS = 0.042
# The candidates of one request hold at most this many characters. The largest request of the 2026-10-05 subset had
# 38,701 input tokens. Jev accepts 64,000 tokens per request.
JEV_REQUEST_CHARACTERS = 120_000
# A run logs its progress after this many answered requests.
PROGRESS_EVERY = 500

CLAUDE_CACHE_DIR = DATA_DIR / "cache" / "claude"
CLAUDE_TIMEOUT_SECONDS = 300
CLAUDE_CLI_VERSION = "2.1.289"
# Sonnet 5 and Opus 5 can run with thinking switched off completely.
CLAUDE_MODELS = ("claude-sonnet-5", "claude-opus-5")
# Print mode with no tools, MCP servers, skills, settings files or saved session.
CLAUDE_ARGS = (
    "-p",
    "--output-format",
    "json",
    "--effort",
    "low",
    "--safe-mode",
    "--tools",
    "",
    "--strict-mcp-config",
    "--disable-slash-commands",
    "--setting-sources",
    "",
    "--no-session-persistence",
)
# Switches thinking off.
CLAUDE_ENV = {"MAX_THINKING_TOKENS": "0"}
# The CLI runs from an empty folder outside the repo, so it finds no project files. Claude Code shows this path to
# the model, so the name says nothing about the study and is the same on every machine.
CLAUDE_WORK_DIR = Path("/tmp/workdir")
# The only variables of our environment that the CLI receives: enough to find the program and its sign-in. Anything
# else, such as CLAUDE_CODE_EFFORT_LEVEL or ANTHROPIC_BASE_URL, could change a call without changing its hash.
CLAUDE_INHERITED_VARS = ("PATH", "HOME", "USER", "TMPDIR", "LANG")

METATOOL_COMMIT = "35e81bb7576826e980c80fed8f8c0a2b4a1e6fbb"
METATOOL_BASE_URL = f"{GITHUB_RAW_URL}/HowieHwong/MetaTool/{METATOOL_COMMIT}/"
METATOOL_RAW_DIR = DATA_DIR / "metatool" / "raw"
# Every file under dataset/ at METATOOL_COMMIT, with its SHA-256.
METATOOL_SHA256 = {
    "dataset/big_tool_des.json": "dcb6b4d2586acaa697d40ac710ceed2c201487b0eb2ea2651f56025bfabc7f5a",
    "dataset/data/all_clean_data.csv": "cf2eb0474396677530931def51012da4e88f9f34f655332f04177b2054101baf",
    "dataset/data/multi_tool_query_golden.json": "ef37d10a8cb5b41435d6ea3ae29819afdb8d6db0852268830e5ee77259507f51",
    "dataset/plugin_des.json": "c446ade5acfb8e16c477124250665021e63b11bf6cb232db04fc9ba6bed0389a",
    "dataset/plugin_info.json": "864bf25bd5494feca861acb98f69d260f212d9c098a2dc68b4b2ee357d6fb2f5",
    "dataset/scenario/Finance Staff.json": "07c202f9ea9e8ec6d7df12b71e6c2c6ad4e932dd1de9a50202ae039236cb12c5",
    "dataset/scenario/Housewife.json": "c800e52e65e6a98a4259012959aaf13cdbb8902d90046ca3d6f2971746ab46a7",
    "dataset/scenario/Software Engineer.json": "c30b5efc174facf767567560d7d192138711a102800f14149f27764ed8514844",
    "dataset/scenario/Students.json": "6d997bbd0749c663d1239631277ac6cc51e0159dd83f363984f52cdb4c5f357f",
    "dataset/scenario/TopTool_top10.json": "9fc922c4a9277c34d88f45e7a17b1b68cbcfbe0bdc7a139f287ab92b66a8b264",
    "dataset/scenario/TopTool_top15.json": "54e8193bf4fd54397d1cf67fcadc99b1d463779225dd606fd7cf93ebe1e8b02d",
    "dataset/scenario/TopTool_top5.json": "23b95a4b43bbbc8e66aba11c7dd54fa62255471d500833c105d3227bcd6dac7e",
    "dataset/scenario/artists&designers.json": "c1d40d924632b63b258a69102c8a8f0b260001dfc8d62a759db5d14411a97302",
    "dataset/scenario/elders.json": "98cf8ecec235e081f70a6f285103090aeab983666338101a4e10cab307b19387",
    "dataset/tmp_dataset/Task1.json": "3b5966d92acb28be4e61c877d9b9c2d4b42a0fe720b925db432bf82441ceefac",
    "dataset/tmp_dataset/Task2-Subtask1.json": "618e882d3d443e11b5c6fb2c983057004c0b3d67056a56c82e8afccba1773ad6",
    "dataset/tmp_dataset/Task2-Subtask2.json": "0720e711f864210c1a2dd1de5ae54bf9c65eaefd160d89c58c6e88fe93689ef5",
    "dataset/tmp_dataset/Task2-Subtask3.json": "f893730a94cc6342d4171f4eb7187277fc7cc4a218b9060668039cab069f4a75",
    "dataset/tmp_dataset/Task2-Subtask4.json": "d7851cee10048f9d650b15f795c50daf097abb2ef4b893f9bb45abfedea0ea63",
    "dataset/tool_embedding.pkl": "177ac60c75de27ffd32c48fb550e5e948084876ebbc95c2458a098f4442d3dd7",
}

STABLETOOLBENCH_COMMIT = "aa4ed9f4737ad98bd706663f01d63623c3427812"
STABLETOOLBENCH_BASE_URL = (
    f"{GITHUB_RAW_URL}/THUNLP-MT/StableToolBench/{STABLETOOLBENCH_COMMIT}/solvable_queries/test_instruction/"
)
STABLETOOLBENCH_RAW_DIR = DATA_DIR / "stabletoolbench" / "raw"
# The six test files of solvable ToolBench queries at STABLETOOLBENCH_COMMIT, with their SHA-256.
STABLETOOLBENCH_SHA256 = {
    "G1_category.json": "123cb9073c8b6e6473df91c8a51170277087e1c263eba2eb6077170edbe849c3",
    "G1_instruction.json": "500aa0105ed451538448f6ea04f10661536b013f3e1a293840fe401688160e7c",
    "G1_tool.json": "05d0c180bbec9d060fd267cc79399bda05beddd0a6d0de68b5488926a9029a1a",
    "G2_category.json": "71e18112f7940934f159d623b1c2b4740b1b4dc58a0b596c63b8151abbf8267e",
    "G2_instruction.json": "82d569cd0fc8fc742a15a3011fb5cd6a8b11e0a5b344c884602347439f43cad7",
    "G3_instruction.json": "f923d1a9452646bd1a415b266117d90675d0f8fc04cf014db58d3cd78c25634f",
}

# MMLU (Hendrycks et al., 2021), from the Hugging Face dataset cais/mmlu at this revision.
MMLU_REVISION = "c30699e8356da336a370243923dbaf21066bb9fe"
MMLU_BASE_URL = f"{HUGGINGFACE_URL}/datasets/cais/mmlu/resolve/{MMLU_REVISION}/"
MMLU_RAW_DIR = DATA_DIR / "mmlu" / "raw"
# The test questions of all 57 subjects in one file.
MMLU_RAW_FILE = "all/test-00000-of-00001.parquet"
MMLU_SHA256 = {MMLU_RAW_FILE: "74a41822ce7d3def56e1682f958469c04642a5336a5ce912fa375fdb90fb25d7"}

BFCL_COMMIT = "6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"
BFCL_BASE_URL = (
    f"{GITHUB_RAW_URL}/ShishirPatil/gorilla/{BFCL_COMMIT}/berkeley-function-call-leaderboard/bfcl_eval/data/"
)
BFCL_RAW_DIR = DATA_DIR / "bfcl" / "raw"
# The folders, next to the test files, of the ground-truth files and of the function definition files.
BFCL_ANSWER_DIR = "possible_answer"
BFCL_FUNC_DOC_DIR = "multi_turn_func_doc"
# The 20 BFCL v4 test files at BFCL_COMMIT, with their SHA-256.
BFCL_TEST_SHA256 = {
    "BFCL_v4_format_sensitivity.json": "1e7ebd0ec441198d3f7d3b60be73d0c9eba54094d2c3731b830f5da7a2c63c19",
    "BFCL_v4_irrelevance.json": "2b6ed4c2e992cdcf5f1678a701851f944bef7550ee026ed1ddb89efed5be01a6",
    "BFCL_v4_live_irrelevance.json": "6559fda2beaceb609a2cd2e504c65b4a56cb448e1ef88fddfd199e163d163349",
    "BFCL_v4_live_multiple.json": "fd8ccfad4d911420d0e3341dbe2fff77d1d341da934248b9bb2bda24ab3a10c8",
    "BFCL_v4_live_parallel.json": "6c26e9fdc3350cf596e6d1ea9c179cbff834761bccf562f4141ed29a839ca421",
    "BFCL_v4_live_parallel_multiple.json": "21d4b9319c1faac431e22757b367ea28917fe467364c3a4b17f16ec06d4f6e79",
    "BFCL_v4_live_relevance.json": "e03f9e241657a137cba48a89ee12f47bf3fcb7e4f6274263e9c699a0c974203a",
    "BFCL_v4_live_simple.json": "1af2ac87dca47556db7b7e37e51e28b459a38b594e3c7b3c792b4903598ca0c4",
    "BFCL_v4_memory.json": "40fc21d4528af53c6b44204def89e81515d0101654229e2c2e82bbf5f047b14f",
    "BFCL_v4_multi_turn_base.json": "1a21a995d06fd6f20ba55de7bced30ef953ec35e998f502ec2ecf4d66ef1c43a",
    "BFCL_v4_multi_turn_long_context.json": "78c3268c5cc8e97c0f4ec6c811b3b9a2bba14323b1830b7a874b06d822749324",
    "BFCL_v4_multi_turn_miss_func.json": "87d28ce10e37d864b72de85d5732eef2a867b241d6c1c99b4ae682c9e3ea921c",
    "BFCL_v4_multi_turn_miss_param.json": "f0c66dda3795f5f53e3e1c0cc8ba0246b6761c8f58bdba8317203bf451ab8838",
    "BFCL_v4_multiple.json": "aef168155ebd74b7ac2401198b201343bc7d16d7a3d7e0d4e6d8ee82c6969b2a",
    "BFCL_v4_parallel.json": "19f51a82eff42e5d62541aa500115a056eb78f437c2ba1f10415fd7c8e5dda84",
    "BFCL_v4_parallel_multiple.json": "8863ea8433239f55c5f016154cf0830853c89f693c6ea270396a2fa121960579",
    "BFCL_v4_simple_java.json": "13d2303a125b08754f0e41995b9273b5005fa8ed8ebfaa24ef53b4d83c4b5c6e",
    "BFCL_v4_simple_javascript.json": "329e67fedf79a6243d93dbda4b388d12bd2d31f1f2163d92cb6ef676d1764f44",
    "BFCL_v4_simple_python.json": "82dd63ba502eb2520c6b5d1d9a5c4b590e03ff261565175561f6228a367d1991",
    "BFCL_v4_web_search.json": "6fc41d96d003dc849028966a782923560d2fc127ed2088aa967f06daaafa4268",
}
# The 16 ground-truth files in possible_answer/, named after the test files they belong to.
BFCL_ANSWER_SHA256 = {
    "BFCL_v4_live_multiple.json": "97e90d59c5bd76c55a2920ce93e5566e9046307d3f558578f085f9d3a56c3084",
    "BFCL_v4_live_parallel.json": "8a9f189ff0e832ebbbbdade1fd95a7dbcc67406e9177df3f0aad76f59ab00350",
    "BFCL_v4_live_parallel_multiple.json": "f5b5f360556c5feb51db46fb9f56ee4b304f4b45b161599bbb14161c98a2873f",
    "BFCL_v4_live_simple.json": "fec9cfa9744a936f9126981e85a2023da1e63e273eafebc81923a1162fad70ce",
    "BFCL_v4_memory.json": "2355cf8d842f94af6bcb7bfa6ad2f9e472bc6d825d6ecd45702cfc41e27d7e5d",
    "BFCL_v4_multi_turn_base.json": "1fee67823b317571649177dd89d63969feaae4e810cc7448ee55ba797fb7c8fc",
    "BFCL_v4_multi_turn_long_context.json": "e82aa0e839c39d23c64a05834f7ae024d7c9738ec21738ecee78dc876e3d0d18",
    "BFCL_v4_multi_turn_miss_func.json": "69e679b806d1c871b05393a4b95583bb973248e5b8d96c2d7f4ca05e29fc32e6",
    "BFCL_v4_multi_turn_miss_param.json": "59c442901779e2c31c33abcd566d032e03736e5ad8069de2fe05489873046ecf",
    "BFCL_v4_multiple.json": "244e00ce9395df948bcafc7bee64e8f9c87ef70887587d83cae45b13699f3047",
    "BFCL_v4_parallel.json": "8a6aa19c1adddc6a5a2f7e40f9dbf30cc7e95815e7b830c90589ab318229e0f0",
    "BFCL_v4_parallel_multiple.json": "5ebf24f458c1f16300c05505d83d6f0a1b68b79be273a033febd0d4f840507e3",
    "BFCL_v4_simple_java.json": "78f25616084044fa05bbfcee68e03f6ececb222bdd5cb3b7783a675fb3366e35",
    "BFCL_v4_simple_javascript.json": "e2f9f2e51d88e0c8056ffbf1a3dd3d02eb032532d2b5d98c9cc9003385bdd56b",
    "BFCL_v4_simple_python.json": "90cd5bc653690ee8e459b5b3f3fc9458606f7f3fcbf795bb51b7dc581f8c86dc",
    "BFCL_v4_web_search.json": "771cab45fdad5744563456801d4623a42c5a358f10514b9b9105d2f6052b4999",
}
# The 12 function definition files in multi_turn_func_doc/, used by the multi-turn and agentic test files.
BFCL_FUNC_DOC_SHA256 = {
    "gorilla_file_system.json": "c4c1b741c71e2a17c97a5dc9c4a91d89978c4eaece56494d14272d5df6c650e9",
    "math_api.json": "83fa31708c89442bdcf12ac4dfbe3be8663ec9183a1b1524a9fda98164bc7e0b",
    "memory_kv.json": "96480cd9cbd3d4a34cd8f78879bc6622731768a26e080f7a34782e36e3402287",
    "memory_rec_sum.json": "4ceff946df00983c7f0b95d1b70ae402247f3312fb898bac9ecfa1de52f5a783",
    "memory_vector.json": "917908ca99fdd01e203274b7ec6eb2347fa91d57f3c6341e20945cc9c9d746cf",
    "message_api.json": "4d58ea933a5d2b280d7a52366617fb47fecd333d7b0e08e724db6fa12fb5f847",
    "posting_api.json": "87f9fc404a06e4107d7c366f1399c596440e84c16cb119faf374b2f532d86e8b",
    "ticket_api.json": "31324e0380782664fe82ba05bd23517808ad55692b45a5fe7c3d4d395fe4f0f8",
    "trading_bot.json": "1a7933fd8f0cb8fbec38aeae05cb8c24132747cad4904fe1c13ac3d01fc22c2d",
    "travel_booking.json": "f17b950c13adddf41d0848077df58788252e4c2e7cad5cfa71c8c4bf04f57b26",
    "vehicle_control.json": "0c8a66292844874ef7b168f343bc394d8615d2d9e1f4387999a9ee23011eac78",
    "web_search.json": "61fcee411e35f7ff67415e18cd67276615cf06e1c8841a683d2d997dbb46eac5",
}
BFCL_SHA256 = (
    BFCL_TEST_SHA256
    | {f"{BFCL_ANSWER_DIR}/{name}": sha256 for name, sha256 in BFCL_ANSWER_SHA256.items()}
    | {f"{BFCL_FUNC_DOC_DIR}/{name}": sha256 for name, sha256 in BFCL_FUNC_DOC_SHA256.items()}
)

METATOOL_PROCESSED_DIR = DATA_DIR / "metatool" / "processed"
METATOOL_TOOLS_FILE = "dataset/plugin_des.json"
# Name of each MetaTool test file in the processed data, and its path in the raw download.
METATOOL_TEST_FILES = {
    "similar_tools": "dataset/tmp_dataset/Task2-Subtask1.json",
    "scenario": "dataset/tmp_dataset/Task2-Subtask2.json",
    "reliability": "dataset/tmp_dataset/Task2-Subtask3.json",
    "multi_tool": "dataset/tmp_dataset/Task2-Subtask4.json",
    "tool_awareness": "dataset/tmp_dataset/Task1.json",
}
# One line of the numbered tool list in a MetaTool prompt: the number and the tool name.
METATOOL_TOOL_LINE = r"^(\d+)\. tool name: (.*?), tool description: "

STABLETOOLBENCH_PROCESSED_DIR = DATA_DIR / "stabletoolbench" / "processed"
# The six test files, named as in the raw download without ".json", in the order the dashboard shows them.
STABLETOOLBENCH_TEST_FILES = (
    "G1_instruction",
    "G1_tool",
    "G1_category",
    "G2_instruction",
    "G2_category",
    "G3_instruction",
)

BFCL_PROCESSED_DIR = DATA_DIR / "bfcl" / "processed"

MMLU_PROCESSED_DIR = DATA_DIR / "mmlu" / "processed"
# The processed file with every test question, and the one with the questions whose choices can be moved, copied and
# replaced: the 4 choices differ, and none refers to another choice.
MMLU_TEST_FILE = "test"
MMLU_STANDALONE_FILE = "test_standalone"
MMLU_TEST_FILES = (MMLU_TEST_FILE, MMLU_STANDALONE_FILE)
# A choice that matches this pattern, with upper and lower case taken as the same, refers to other choices.
MMLU_REFERRING_CHOICE = (
    r"\b(none|all|both|neither|either) of (the|these)|\b(above|the other)\b|^(I|II|III|IV)\b"
    r"|\b(A|B|C|D) and (A|B|C|D)\b"
)
# A raw test file is named BFCL_FILE_PREFIX, the test file's name and ".json". Its ground truth has the same file
# name in the folder BFCL_ANSWER_DIR.
BFCL_FILE_PREFIX = "BFCL_v4_"
# A single-turn file whose correct output has no call, and the one that accepts any call. Neither kind has a
# ground-truth file.
BFCL_NO_CALL_FILES = ("irrelevance", "live_irrelevance")
BFCL_ANY_CALL_FILES = ("live_relevance",)
BFCL_SINGLE_TURN_FILES = (
    "simple_python",
    "simple_java",
    "simple_javascript",
    "multiple",
    "parallel",
    "parallel_multiple",
    "irrelevance",
    "live_simple",
    "live_multiple",
    "live_parallel",
    "live_parallel_multiple",
    "live_irrelevance",
    "live_relevance",
)
BFCL_MULTI_TURN_FILES = (
    "multi_turn_base",
    "multi_turn_miss_func",
    "multi_turn_miss_param",
    "multi_turn_long_context",
)
# The two agentic files. Their answers are text, and a row names API classes instead of listing functions.
BFCL_WEB_SEARCH_FILE = "web_search"
BFCL_MEMORY_FILE = "memory"
# Every test file that has examples, in the order the dashboard shows them. format_sensitivity lists ids of examples
# in other files.
BFCL_TEST_FILES = (*BFCL_SINGLE_TURN_FILES, *BFCL_MULTI_TURN_FILES, BFCL_WEB_SEARCH_FILE, BFCL_MEMORY_FILE)
# API class named by a multi-turn or web search row -> the file in BFCL_FUNC_DOC_DIR that defines its functions.
BFCL_CLASS_DOCS = {
    "GorillaFileSystem": "gorilla_file_system.json",
    "MathAPI": "math_api.json",
    "MessageAPI": "message_api.json",
    "TwitterAPI": "posting_api.json",
    "TicketAPI": "ticket_api.json",
    "TradingBot": "trading_bot.json",
    "TravelAPI": "travel_booking.json",
    "VehicleControlAPI": "vehicle_control.json",
    "WebSearchAPI": "web_search.json",
}
# BFCL runs a memory row once on each memory backend. Backend -> the file in BFCL_FUNC_DOC_DIR with its functions.
BFCL_MEMORY_DOCS = {"kv": "memory_kv.json", "vector": "memory_vector.json", "rec_sum": "memory_rec_sum.json"}
# Where a model that only selects could take a parameter value from, in the order the sources are tried. A value
# with none of them is "other".
BFCL_VALUE_SOURCES = ("query", "boolean", "schema", "left_out", "description", "other")
# The names BFCL's function definitions use for the true-or-false type, in lower case.
BFCL_BOOLEAN_TYPES = ("boolean", "bool")

# Experiment -> dataset -> the test files it sends, in order. "position" sends every example in the released order and
# with its correct tools at each placement. "length" sends each different one-tool query with lists of several lengths.
# "wording" sends every example with one tool list and each wording of the instruction for several correct tools.
# "growth" sends every example with its tool list and with random other tools added up to several list lengths.
# "reworded" sends every example with a list that holds only rewordings of one of its correct tools.
# "rotated" sends that list in every rotation of the order in which the rewordings are written.
# "copied" sends every example with a list of copies of one of its correct tools, in every rotation.
# "absent" sends every example with a list that has no correct tool: other tools of the example and "None", in every
# rotation. "absent_random" does the same with random tools of the dataset that are not in the list of the example.
# "unrelated" sends every example with a list of such random tools and without "None", in every rotation.
# "own" sends every example with its own list in every rotation.
# The MetaTool test files whose examples have a correct tool to reword.
METATOOL_REWORDED_FILES = ("similar_tools", "scenario", "multi_tool")
EXPERIMENT_TEST_FILES: dict[str, dict[str, tuple[str, ...]]] = {
    "position": {"metatool": ("similar_tools", "scenario", "multi_tool", "reliability")},
    "length": {"metatool": ("similar_tools", "scenario")},
    "wording": {"stabletoolbench": STABLETOOLBENCH_TEST_FILES},
    "growth": {"stabletoolbench": STABLETOOLBENCH_TEST_FILES},
    "reworded": {"metatool": METATOOL_REWORDED_FILES, "stabletoolbench": STABLETOOLBENCH_TEST_FILES},
    "rotated": {"metatool": METATOOL_REWORDED_FILES, "stabletoolbench": STABLETOOLBENCH_TEST_FILES},
    "copied": {
        "metatool": METATOOL_REWORDED_FILES,
        "stabletoolbench": STABLETOOLBENCH_TEST_FILES,
        "mmlu": (MMLU_STANDALONE_FILE,),
    },
    "absent": {"metatool": ("similar_tools",), "mmlu": (MMLU_STANDALONE_FILE,)},
    "absent_random": {"metatool": ("similar_tools",), "mmlu": (MMLU_STANDALONE_FILE,)},
    "unrelated": {"metatool": METATOOL_REWORDED_FILES, "mmlu": (MMLU_STANDALONE_FILE,)},
    "own": {"mmlu": (MMLU_STANDALONE_FILE,)},
}
# Dataset -> test files whose benchmark lets the model answer that no tool applies. Their lists end with this candidate.
NONE_TEST_FILES: dict[str, tuple[str, ...]] = {
    "metatool": ("similar_tools", "scenario", "reliability"),
    "stabletoolbench": (),
    "mmlu": (),
}
NONE_NAME = "None"
NONE_DESCRIPTION = "No tool in the list is applicable to the user's query."
# Dataset -> the name and the description of its "None" candidate, where the options are not tools.
NONE_CANDIDATES = {"mmlu": ("None of the above", "")}
# Dataset -> the instruction of every list of the dataset, where the options are not tools.
DATASET_INSTRUCTIONS = {"mmlu": "Choose the correct answer to the question."}
# Dataset -> test files whose queries can have several correct tools. Jev's answer to a query with k correct tools is
# its k highest-probability tools.
SEVERAL_TOOL_TEST_FILES: dict[str, tuple[str, ...]] = {
    "metatool": ("multi_tool",),
    "stabletoolbench": STABLETOOLBENCH_TEST_FILES,
    "mmlu": (),
}
ONE_TOOL_INSTRUCTIONS = (
    "Choose the tool that is applicable to the user's query. If no tool in the list is applicable, choose None."
)
# The wordings of the instruction for two tools that are compared, by name, and the one a run uses by default.
TWO_TOOL_INSTRUCTIONS = {
    "one": "Two tools in the list are appropriate to solve the user's query. Choose one of them.",
    "both": "Two tools in the list are appropriate to solve the user's query. Choose both.",
}
TWO_TOOL_WORDING = "one"
# The "wording" experiment. Name of a wording -> an instruction that states the number of correct tools, written as a
# word in place of {number}. These wordings are sent for a query with two or more correct tools.
COUNTED_OPENING = "{number} tools in the list are appropriate to solve the user's query."
COUNTED_WORDINGS = {
    "one": f"{COUNTED_OPENING} Choose one of them.",
    "all": f"{COUNTED_OPENING} Choose all of them.",
    "equal": f"{COUNTED_OPENING} Choose all of them with equal probability.",
}
# Name of a wording -> an instruction that does not state the number of correct tools. It is sent for every query.
UNCOUNTED_WORDINGS = {"every": "Choose every tool in the list that is needed to solve the user's query."}
NUMBER_WORDS = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}
# In the "wording" experiment a list with fewer tools than this gets random other tools of the dataset added.
PADDED_LIST_TOOLS = 5
# The "growth" experiment. Dataset -> the list lengths that the padded list of an example is grown to with random
# other tools of the dataset.
GROWTH_LENGTHS = {"stabletoolbench": (20, 50, 100, 199)}
# The wordings that the "growth" experiment sends with every list.
GROWTH_WORDINGS = ("all", "every")
# The name of the padded list of an example before it is grown.
OWN_LIST = "own"
# The "reworded" experiment. One correct tool of a query is chosen with the seed, and the list that is sent holds only
# rewordings of its name and description, in a seeded order. Dataset -> the file of rewordings: the name of a tool ->
# its 5 rewordings. Claude Opus 5.5 wrote them on 2026-10-06 and 2026-10-07. A rewording of a StableToolBench API
# keeps the category and the tool of the name, and rewords the API name and the description. A blank description stays
# blank. A rewording of a MetaTool tool rewords the name and the description.
REWORDINGS_FILES = {
    "metatool": Path(__file__).parent / "rewordings" / "metatool.json",
    "stabletoolbench": Path(__file__).parent / "rewordings" / "stabletoolbench.json",
}
# The experiments whose lists hold only rewordings or copies of one tool. Every entry is correct, and "None" is not
# offered.
REWORDING_EXPERIMENTS = ("reworded", "rotated", "copied")
# The "copied" experiment lists one correct tool this many times. The names of the copies differ only by extra spaces.
COPIED_TOOLS = 5
# The "absent" experiments list this many tools that are not correct, and "None" with them. An MMLU question has 3
# choices that are not correct, and its "absent" list holds the 3.
ABSENT_LIST_TOOLS = 4
# The experiments whose lists do not get "None" added at the end: the lists of rewordings and of copies, and the
# "absent" lists, which hold "None" at a place of its own, and the "unrelated" lists, which offer no "None".
NO_ADDED_NONE_EXPERIMENTS = (*REWORDING_EXPERIMENTS, "absent", "absent_random", "unrelated")
# The "unrelated" experiment lists this many random tools, as many as the "copied" experiment lists copies.
UNRELATED_TOOLS = 5
REWORDED_INSTRUCTIONS = "Pick all the tools in the list that are relevant to the task at hand."
# The name of the list that holds the rewordings.
REWORDED_LIST = "reworded"
# The "rotated" experiment names a list by this and the number of places its rewordings are moved towards the start.
ROTATED_LIST = "rotated"
# Dataset -> the list lengths of the "length" experiment. MetaTool has 199 tools, so its last list holds every tool.
LIST_LENGTHS = {"metatool": (5, 10, 20, 50, 100, 199)}
# The name of the order in which a test file lists the tools.
RELEASED_ORDER = "released"
# Name of a placement -> how far down the list the correct tool goes: the share of the positions after the first.
PLACEMENTS = {
    "first": Fraction(0),
    "quarter": Fraction(1, 4),
    "middle": Fraction(1, 2),
    "three_quarters": Fraction(3, 4),
    "last": Fraction(1),
}
# The pairs of placements used for two correct tools with distractors between them.
SEPARATED_PLACEMENTS = (("first", "last"), ("first", "middle"), ("middle", "last"))
# The placement rule is decided for lists of at least this many tools, with at most this many correct tools.
PLACEMENT_MIN_TOOLS = 5
PLACEMENT_MAX_CORRECT = 2
# Seed of the order of the distractors, and of which of two correct tools comes first.
ORDER_SEED = 2026

# A bootstrap interval resamples the examples this many times from this seed, and leaves this share of the resampled
# means outside at each end, which gives a 95% interval.
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 1
INTERVAL_TAIL = Fraction(1, 40)
# An answer counts as confident in the figures of a run when its highest probability is at least this. It is the
# value at which arXiv 2609.26550 counts. Rushab has not decided the threshold.
CONFIDENT_PROBABILITY = 0.9

# The tool list of a processed dataset. Every other .jsonl file in the folder is a test file.
TOOLS_FILE_NAME = "tools.jsonl"
WORD_PATTERN = r"[a-z][a-z'-]*"
# English stop words, separated by spaces.
STOP_WORDS_TEXT = """
a about above after again against all am an and any are aren't as at be because been before being below between both
but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further
had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i
i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor not of off on
once only or other ought our ours ourselves out over own same shan't she she'd she'll she's should shouldn't so some
such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've
this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when
when's where where's which while who who's whom why why's with won't would wouldn't you you'd you'll you're you've
your yours yourself yourselves
"""

# The number of tools named at each end of a count over the tools.
EXTREMES_SHOWN = 5
# A histogram has at most this many bins.
HISTOGRAM_BINS = 40
# A histogram gets logarithmic bins when its largest value is this many times its median.
LOG_BINS_RATIO = 8
# The dashboard loads one file of statistics per dataset from this folder.
DASHBOARD_STATS_DIR = REPO_ROOT / "docs" / "stats"

# Dataset name -> the arguments of grjev.download.download_files: base URL, SHA-256 by path, destination folder.
DOWNLOADS = {
    "metatool": (METATOOL_BASE_URL, METATOOL_SHA256, METATOOL_RAW_DIR),
    "stabletoolbench": (STABLETOOLBENCH_BASE_URL, STABLETOOLBENCH_SHA256, STABLETOOLBENCH_RAW_DIR),
    "bfcl": (BFCL_BASE_URL, BFCL_SHA256, BFCL_RAW_DIR),
    "mmlu": (MMLU_BASE_URL, MMLU_SHA256, MMLU_RAW_DIR),
}

# Dataset name -> where its files in the common format are written.
PROCESSED_DIRS = {
    "metatool": METATOOL_PROCESSED_DIR,
    "stabletoolbench": STABLETOOLBENCH_PROCESSED_DIR,
    "bfcl": BFCL_PROCESSED_DIR,
    "mmlu": MMLU_PROCESSED_DIR,
}
# Dataset name -> its test files, in the order they are shown.
TEST_FILES = {
    "metatool": tuple(METATOOL_TEST_FILES),
    "stabletoolbench": STABLETOOLBENCH_TEST_FILES,
    "bfcl": BFCL_TEST_FILES,
    "mmlu": MMLU_TEST_FILES,
}
