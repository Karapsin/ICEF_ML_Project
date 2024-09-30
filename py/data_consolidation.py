import os
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 320)

files = os.listdir('../data_load')
df = pd.read_csv(f'data_load\\{files[0]}')
for file in files[1:]:
    df = pd.concat([df, pd.read_csv(f'data_load\\{file}')], ignore_index = True)


#remove useless columns and duplicates
df=(df
     .drop(['Unnamed: 0', 'location', 'underground',
            'residential_complex', 'deal_type',
            'accommodation_type', 'commissions'
           ],
           axis = 1
      )
     .drop_duplicates()
    )

#remove those which are not from Moscow
df = df[df['url'].str.contains('www.cian.ru')]

#if url is duplicated, we are taking min price
fixed_prices = (df[['url', 'price_per_month']]
                 .groupby('url')
                 .min()
               )

#attaching fixed prices
#filtering null adreses
#saving
outliers_urls = pd.read_csv('../csv/outliers_to_delete.csv')['url']
(df
  .drop(columns = ['price_per_month'])
  .merge(fixed_prices, on = 'url', how = 'inner')
  .rename(columns={'total_meters': 'meters',
                   'price_per_month':'price',
                   'rooms_count': 'rooms',
                   'floors_count': 'floors_total'
                   }
   )
  .query('''
         1==1 \
         and street.notnull() \
         and house_number.notnull() \
         and url not in @outliers_urls\
         and floor > 0 \
         and floors_total > 0 \
         and meters > 0 \
         and rooms > 0 \
         '''
   )
  .to_csv('csv\\consolidated_data.csv', index = False)
)