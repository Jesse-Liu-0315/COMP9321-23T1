import json
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import numpy as np
import math
import re

studentid = os.path.basename(sys.modules[__name__].__file__)


def log(question, output_df, other):
    print("--------------- {}----------------".format(question))

    if other is not None:
        print(question, other)
    if output_df is not None:
        df = output_df.head(5).copy(True)
        for c in df.columns:
            df[c] = df[c].apply(lambda a: a[:20] if isinstance(a, str) else a)

        df.columns = [a[:10] + "..." for a in df.columns]
        print(df.to_string())


def question_1(city_pairs):
    """
    :return: df1
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    #################################################
    # Your code goes here ...
    #################################################
    df1 = pd.read_csv(city_pairs)
    def question1_pass(column):
        if column["Passengers_In"] == column["Passengers_Out"]:
            return "SAME"
        elif column["Passengers_In"] > column["Passengers_Out"]:
            return "IN"
        elif column["Passengers_In"] < column["Passengers_Out"]:
            return "OUT"
    def question1_freight(column):
        if column["Freight_In_(tonnes)"] == column["Freight_Out_(tonnes)"]:
            return "SAME"
        elif column["Freight_In_(tonnes)"] > column["Freight_Out_(tonnes)"]:
            return "IN"
        elif column["Freight_In_(tonnes)"] < column["Freight_Out_(tonnes)"]:
            return "OUT"
    def question1_mail(column):
        if column["Mail_In_(tonnes)"] == column["Mail_Out_(tonnes)"]:
            return "SAME"
        elif column["Mail_In_(tonnes)"] > column["Mail_Out_(tonnes)"]:
            return "IN"
        elif column["Mail_In_(tonnes)"] < column["Mail_Out_(tonnes)"]:
            return "OUT"

    df1['passenger_in_out'] = df1.apply(question1_pass, axis=1)
    df1['freight_in_out'] = df1.apply(question1_freight, axis=1)
    df1['mail_in_out'] = df1.apply(question1_mail, axis=1)
    

    log("QUESTION 1", output_df=df1[["AustralianPort", "ForeignPort", "passenger_in_out", "freight_in_out", "mail_in_out"]], other=df1.shape)
    return df1


def question_2(df1):
    """
    :param df1: the dataframe created in question 1
    :return: dataframe df2
            Please read the assignment specs to know how to create the output dataframe
    """

    #################################################
    # Your code goes here ...
    #################################################
    ausPort = pd.DataFrame(df1, columns=['AustralianPort'])
    ausPort = ausPort.drop_duplicates()
    # passenger
    grouped_df = df1.groupby(['AustralianPort', 'passenger_in_out']).size().reset_index()
    selected_df = pd.pivot_table(grouped_df, index = ['AustralianPort'],columns='passenger_in_out', fill_value=0).reset_index()
    selected_df.columns = selected_df.columns.droplevel(0)
    selected_df.columns = ['AustralianPort', 'PassengerInCount', 'PassengerOutCount', 'PassengerSameCount']
    df2 = pd.merge(ausPort, selected_df[['AustralianPort', 'PassengerInCount', 'PassengerOutCount']], on='AustralianPort')
    # freight
    grouped_df = df1.groupby(['AustralianPort', 'freight_in_out']).size().reset_index()
    selected_df = pd.pivot_table(grouped_df, index = ['AustralianPort'],columns='freight_in_out', fill_value=0).reset_index()
    selected_df.columns = selected_df.columns.droplevel(0)
    selected_df.columns = ['AustralianPort', 'FreightInCount', 'FreightOutCount', 'FreightSameCount']
    df2 = pd.merge(df2, selected_df[['AustralianPort', 'FreightInCount', 'FreightOutCount']], on='AustralianPort')
    # mail
    grouped_df = df1.groupby(['AustralianPort', 'mail_in_out']).size().reset_index()
    selected_df = pd.pivot_table(grouped_df, index = ['AustralianPort'],columns='mail_in_out', fill_value=0).reset_index()
    selected_df.columns = selected_df.columns.droplevel(0)
    selected_df.columns = ['AustralianPort', 'MailInCount', 'MailOutCount', 'MailSameCount']
    df2 = pd.merge(df2, selected_df[['AustralianPort', 'MailInCount', 'MailOutCount']], on='AustralianPort')
    #sort
    df2 = df2.sort_values(by='PassengerInCount', ascending=False)


    log("QUESTION 2", output_df=df2, other=df2.shape)
    return df2


def question_3(df1):
    """
    :param df1: the dataframe created in question 1
    :return: df3
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """
    #################################################
    # Your code goes here ...
    #################################################
    #pass
    def passInAve(column):
        return round(column['Passengers_In'] / numMonth, 2)
    def passOutAve(column):
        return round(column['Passengers_Out'] / numMonth, 2)
    #freight
    def freInAve(column):
        return round(column['Freight_In_(tonnes)'] / numMonth, 2)
    def freOutAve(column):
        return round(column['Freight_Out_(tonnes)'] / numMonth, 2)
    #mail
    def mailInAve(column):
        return round(column['Mail_In_(tonnes)'] / numMonth, 2)
    def mailOutAve(column):
        return round(column['Mail_Out_(tonnes)'] / numMonth, 2)

    # count the month of it appears
    numMonth = df1.nunique().reset_index()
    numMonth = numMonth.rename(columns = {0: 'num'})
    numMonth = numMonth.iloc[0,1]
    # sum the value
    numSum = df1.groupby('Country').sum().reset_index()
    newdf = numSum[['Country', 'Passengers_In', 'Passengers_Out', 'Freight_In_(tonnes)', 'Freight_Out_(tonnes)', 'Mail_In_(tonnes)', 'Mail_Out_(tonnes)']]
    newdf.loc[:, 'Passengers_in_average'] = newdf.apply(passInAve,axis=1)
    newdf.loc[:, 'Passengers_out_average'] = newdf.apply(passOutAve,axis=1)
    newdf.loc[:, 'Freight_in_average'] = newdf.apply(freInAve,axis=1)
    newdf.loc[:, 'Freight_out_average'] = newdf.apply(freOutAve,axis=1)

    newdf.loc[:, 'Mail_in_average'] = newdf.apply(mailInAve,axis=1)
    newdf.loc[:, 'Mail_out_average'] = newdf.apply(mailOutAve,axis=1)
    df3 = newdf[['Country', 'Passengers_in_average', 'Passengers_out_average', 'Freight_in_average', 'Freight_out_average', 'Mail_in_average', 'Mail_out_average']]
    df3 = df3.sort_values(by='Passengers_in_average', ascending=True)
    log("QUESTION 3", output_df=df3, other=df3.shape)
    return df3


def question_4(df1):
    """
    :param df1: the dataframe created in question 1
    :return: df4
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    #################################################
    # Your code goes here ...
    #################################################
    nonZero = df1
    # delete no passenger exist
    nonZero = nonZero.drop(index = nonZero[nonZero['Passengers_Out'] <= 0].index,axis=0)
    # count more than one foreign port
    grouped = nonZero.groupby(['AustralianPort', 'Country', 'Month']).nunique()['ForeignPort'].reset_index()
    grouped = grouped.drop(index = grouped[grouped['ForeignPort'] <= 1].index,axis=0)
    # count number of unique month
    df4 = grouped.groupby('Country').nunique()['Month'].reset_index().sort_values(by='Month', ascending=False)
    df4 = df4.rename(columns={'Month': 'Unique_ForeignPort_Count'})
    df4 = df4.head(5)
    log("QUESTION 4", output_df=df4, other=df4.shape)
    return df4


def question_5(seats):
    """
    :param seats : the path to dataset
    :return: df5
            Data Type: dataframe
            Please read the assignment specs to know how to create the  output dataframe
    """
    #################################################
    # Your code goes here ...
    #################################################
    def question5_source(column):
        if column['In_Out'] == 'I':
            return column['International_City']
        elif column['In_Out'] == 'O':
            return column['Australian_City']
    def question5_des(column):
        if column['In_Out'] == 'I':
            return column['Australian_City']
        elif column['In_Out'] == 'O':
            return column['International_City']
    df5 = pd.read_csv(seats)
    df5['Source_City'] = df5.apply(question5_source, axis=1)
    df5['Destination_City'] = df5.apply(question5_des, axis=1)
    log("QUESTION 5", output_df=df5, other=df5.shape)
    return df5


def question_6(df5):
    """
    :param df5: the dataframe created in question 5
    :return: df6
    """

    #################################################
    # Your code goes here ...
    #################################################
    """
    For a new or existing airline, the number of passengers and the number of competing 
    airlines play a crucial role in deciding to open a new route. Moreover, these two 
    data points will change over time, and airlines have to be sensitive about the change. 
    Therefore, the data framework I have generated groups by origin and destination city 
    and displays how many available seats there are on this route in the current month, 
    how many flights are scheduled, and how many airlines are operating. Since stop 
    may have an impact on passenger traffic, my data framework also includes the percentage 
    of flights with stop among all routes in the current month.

    If a new or existing airline wants to open a new route, they can first find their 
    desired route by alphabetical order using "Source_City" and "Destination_City" columns 
    . Then they can check whether this route has changed year by year or has 
    popular months based on columns three ("Year") and four ("Month_num"). Next, they can 
    use columns five through seven ("Max_Seats", "All_Flights", "Num_Airline") to determine 
    whether this route is monopolized or highly competitive so as to decide flight frequency. 
    Finally, the last column "Stop_Rate%" helps airlines determine whether they should 
    consider stop for greater profits.

    """
    def aggFun(column):
        d = {}
        d['Max_Seats'] = column['Max_Seats'].sum()
        d['All_Flights'] = column['All_Flights'].sum()
        d['Num_Airlne'] = column['Airline'].nunique()
        d['Stop_Rate'] = ((column['Stops'] >= 1) * column['All_Flights'] ).sum() 
        return pd.Series(d, index = ['Max_Seats', 'All_Flights', 'Num_Airlne', 'Stop_Rate'])
    def stopRate(column):
        if column['All_Flights'] > 0:
            return (column['Stop_Rate'] / column['All_Flights']) * 100
        else:
            return 0

    grouped = df5.groupby(['Source_City', 'Destination_City', 'Year', 'Month_num']).apply(aggFun).reset_index()
    grouped['Stop_Rate%'] = grouped.apply(stopRate, axis=1)
    df6 = grouped[['Source_City', 'Destination_City', 'Year', 'Month_num', 'Max_Seats', 'All_Flights', 'Num_Airlne', 'Stop_Rate%']]
    log("QUESTION 6", output_df=df6, other=df6.shape)
    return df6


def question_7(seats, city_pairs):
    """
    :param seats: the path to dataset
    :param city_pairs : the path to dataset
    :return: nothing, but saves the figure on the disk
    """

    #################################################
    # Your code goes here ...
    #################################################
    """
    The task requires us to create a visualization to understand seat utilization based on 
    the following metrics: 'Passengers_In', 'Passengers_Out', 'Max_Seats', and 'Port_Region'. 
    Therefore, I think we should create multiple subplots of line charts. Each subplot 
    represents a port region, with the x-axis representing time and the y-axis representing 
    seat utilization rate. There will be two different colored lines on each subplot, representing 
    the seat utilization rates for passengers entering and leaving Australia from that region.

    My seat utilization rate is calculated by dividing the number of passengers by the maximum 
    number of seats. So first, I found the total number of passengers entering or leaving the 
    same region in the current month in the city_pairs file, then found out the maximum number 
    of seats in the seats file. Finally, I divided them to get my result.

    Through my image, airlines can intuitively see historical records of seat utilization rates 
    for each region so they can quickly make decisions and maximize profits.

    """
    def inFun(column):
        if column['MaxSeats_In'] != 0:
            return column['Passengers_In'] / column['MaxSeats_In']
        else:
            return 0
    def outFun(column):
        if column['MaxSeats_out'] != 0:
            return column['Passengers_Out'] / column['MaxSeats_out']
        else:
            return 0
        
    
    #city_pairs.csv
    dfCity_pairs = pd.read_csv(city_pairs)
    dfCity_pairs = dfCity_pairs.groupby(['Year', 'Month_num','Country']).sum()[['Passengers_In', 'Passengers_Out']].reset_index()

    #seats.csv
    dfSeats = pd.read_csv(seats)
    dfSeats = dfSeats.groupby(['Year', 'Month_num', 'Month', 'Port_Country', 'Port_Region', 'In_Out']).sum()['Max_Seats'].reset_index()
    dfSeats = dfSeats.pivot_table(index = ['Year', 'Month_num', 'Month', 'Port_Country', 'Port_Region'],columns='In_Out', fill_value=0).reset_index()
    dfSeats.columns = dfSeats.columns.droplevel(0)
    dfSeats.columns = ['Year', 'Month_num', 'Month', 'Country', 'Port_Region', 'MaxSeats_In', 'MaxSeats_out']

    
    combine = pd.merge(dfSeats, dfCity_pairs[['Year', 'Month_num', 'Country', 'Passengers_In', 'Passengers_Out']], on = ['Year', 'Month_num', 'Country'])
    combine['in_seat_utilisation'] = combine.apply(inFun, axis=1)
    combine['out_seat_utilisation'] = combine.apply(outFun, axis=1)
    combine = combine[['Month', 'Port_Region', 'in_seat_utilisation', 'out_seat_utilisation']]
    # list of region
    regions = combine['Port_Region'].unique()
    nrows = (len(regions) + 1) // 2
    ncols = 2
    # create subplots
    fig, axs = plt.subplots(nrows, ncols, figsize=(25, 20))
    fig.subplots_adjust(hspace=0.5)
    # Iterate through each region and plot in a separate subplot
    for i, region in enumerate(regions):
        # Calculate the row and column indices for the current subplot
        row = i // ncols
        col = i % ncols
        
        # Filter the dataframe for the current region
        region_df = combine[combine["Port_Region"] == region]
        
        axs[row, col].plot(region_df["Month"], region_df["in_seat_utilisation"], label="In-Seat Utilisation")
        axs[row, col].plot(region_df["Month"], region_df["out_seat_utilisation"], label="Out-Seat Utilisation")
        axs[row, col].legend() # Place a legend on the Axes.
        axs[row, col].set_xlabel("Time")
        axs[row, col].set_ylabel("Seat Utilisation")
        axs[row, col].set_title( "The seat utilisation rate for travel between "+ region + " and Australia over time.")



    plt.savefig("{}-Q7.png".format('Z5320711'))


if __name__ == "__main__":
    df1 = question_1("city_pairs.csv")
    df2 = question_2(df1.copy(True))
    df3 = question_3(df1.copy(True))
    df4 = question_4(df1.copy(True))
    df5 = question_5("seats.csv")
    df6 = question_6(df5.copy(True))
    question_7("seats.csv", "city_pairs.csv")