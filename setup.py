import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="airtouch4pyapi", # Replace with your own username
    version="1.0.8",
    author="Sam Sinnamon",
    author_email="samsinnamon@hotmail.com",
    description="An api allowing control of AC state (temperature, on/off, mode) of an Airtouch 4 controller locally over TCP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LonePurpleWolf/airtouch4pyapi",
    packages=setuptools.find_packages(),
    install_requires=['numpy'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
