Survey Trend Reports Generator
======================================

This is a trend reports generator primarily designed for generating trend reports on my school's graduating student survey data from Qualtrics. However, it is configurable and can work with any type of data, especially survey data. I have included a sample config and sample data so you can test it. Look at the end of the README to see screenshots from use.

Overview
--------

The project is composed of the following main files:

1.  `app.py`: This is the main Flask app that handles routes, processes configuration files, and generates the reports.
2.  `TableGenerator.py`: This file contains the `TableGenerator` class, which is responsible for generating data tables based on the provided configurations.
3.  Jinja templates: These are rendered as the HTML pages for the web app, and contain all the javascript that make it work.

Installation
------------

To set up the project, follow these steps:

1.  Clone the repository.
2.  Install the required dependencies, such as Flask and pandas, using `pip install -r requirements.txt`.
3.  Run the Flask app using `python app.py`.

Usage
-----

1.  Visit the web app's home page.
2.  Choose to load an existing configuration or create a new one.
3.  If creating a new configuration, select the data source and configure the questions, filters, and other settings as needed.
4.  Save the configuration if desired.
5.  Generate the report based on the configuration.
6.  View the generated report with the provided tables and statistics.

Customization
-------------

This application is highly configurable, allowing you to use it with various data sources and formats. You can add new configuration files in the `configs` directory, and data files in the `data` directory. The configurations are specified in JSON format and can be easily modified to suit your needs using the web UI.

License
-------

This project is now part of my student portfolio with my manager's permission and is available for use under the terms of the MIT License.

Screenshots
-----------

### Home Page
<img width="700" alt="Home Page of the app" src="https://user-images.githubusercontent.com/61572668/233503833-79b93e34-c203-445f-b94d-b23f3bc141e5.png">

### Confirmation Page
<img width="700" alt="Confirmation Page for a config" src="https://user-images.githubusercontent.com/61572668/233503873-6b991ad4-c412-4481-9ca1-b140a98fe0c0.png">

### Edit Form/Page
<img width="700" alt="Edit Form/Page" src="https://user-images.githubusercontent.com/61572668/233503912-bbd5b9eb-c7f2-4d6c-87c0-2f236761ee71.png">

### Sample Generated Report
<img width="700" alt="Sample of a generated trend report" src="https://user-images.githubusercontent.com/61572668/233503952-994d05db-1a2c-41d7-b6c8-320b029893ed.png">
