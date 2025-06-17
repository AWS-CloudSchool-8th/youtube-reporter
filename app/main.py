from fsm import run_graph
from pprint import pprint

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    result = run_graph(url)
    pprint(result["final_output"])
