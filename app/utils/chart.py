import matplotlib.pyplot as plt
import tempfile
from app.utils.s3 import upload_bytes

def generate_chart(x: list, y: list, title: str) -> str:
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_title(title)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name)
    with open(tmp.name,"rb") as f:
        content = f.read()
    key = f"charts/{hash(title)}.png"
    return upload_bytes(content, key)