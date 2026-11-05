*** Settings ***
Library           SeleniumLibrary
Library           helper.py
Test Teardown     Close All Browsers

*** Variables ***
${REPORT_FILE}       ${CURDIR}${/}report.html
${PARQUET_FOLDER}    ${CURDIR}${/}parquet_data
${FILTER_DATE}       2026-10-02
${DATE_COLUMN}       visit_date

*** Test Cases ***
HTML Report Should Match Parquet Dataset
    [Documentation]    Compares the table in report.html with the Parquet data.
    ${report_url}=    Evaluate    pathlib.Path(r"${REPORT_FILE}").resolve().as_uri()    modules=pathlib
    Open Browser    ${report_url}    chrome
    Wait Until Element Is Visible    css:.plotly-graph-div svg.main-svg
    ${table}=    Get WebElement    css:.plotly-graph-div
    ${html_df}=    Read Html Table    ${table}
    ${expected_columns}=    Evaluate    list($html_df.columns)
    ${parquet_df}=    Read Parquet Dataset    ${PARQUET_FOLDER}    ${FILTER_DATE}    ${DATE_COLUMN}    False    ${expected_columns}
    Compare Dataframes    ${html_df}    ${parquet_df}