from importlib.machinery import SourceFileLoader

image = SourceFileLoader("image", "./lib/image.py").load_module()
tweet = SourceFileLoader("tweet", "./lib/tweet.py").load_module()


def handler(event, context):
    img_input = image.Image.open(event["location"])
    k = None
    if "k" in event:
        k = event["k"]
    img_result, color_hex = image.get_palette_plot(img_input, k)
    img_result.save("./tmp/result.png")
    return " ".join(color_hex)
