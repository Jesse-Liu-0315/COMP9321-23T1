import pandas as pd

# create an example DataFrame
df = pd.DataFrame({
    'AustralianPort': ['Sydney', 'Sydney', 'Brisbane', 'Brisbane', 'Melbourne', 'Melbourne'],
    'passage_in_out': ['IN', 'SAME', 'OUT', 'IN', 'SAME', 'OUT']
})

# use groupby to group by AustralianPort and count the number of IN and OUT values
grouped_df = df.groupby(['AustralianPort', 'passage_in_out']).size().reset_index(name='counts')

# use pivot_table to reshape the data and separate the IN and OUT counts into separate columns
pivot_df = pd.pivot_table(grouped_df, index='AustralianPort', columns='passage_in_out', 
                          values='counts', fill_value=0)

# rename the columns
pivot_df.columns = ['IN', 'OUT', 'SAME']

print(pivot_df)