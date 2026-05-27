# img2palette

[img2palette](https://twitter.com/img2palette) is a twitter bot that creates a palette from an image when mentioned.

## Features

You can get its reply by mentioning @img2palette with an image. You can also specify the number of colors in the palette by putting a number between 2 and 10 in your tweet.

## How it works

img2palette scales down the image and then maps every pixel into the CIELAB color space. [CIELAB](https://en.wikipedia.org/wiki/CIELAB_color_space) is chosen for its perceptual uniformity. The pixels are partitioned with agglomerative clustering. The clusters' medoids are taken as colors of the palettes.

img2palette to listen to mentions through Twitter's Account Activity API. The application runs on the Serverless Framework on AWS Lambda. The webhook for the account activity api is managed with AWS API gateway. The bot uses the [Tweepy](https://github.com/tweepy/tweepy) Python package to tweet replies. The application is deployed to AWS through CircleCI.