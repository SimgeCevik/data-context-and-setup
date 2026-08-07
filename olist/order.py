import pandas as pd
import numpy as np
from olist.utils import haversine_distance
from olist.data import Olist


class Order:
    '''
    DataFrames containing all orders as index,
    and various properties of these orders as columns
    '''
    def __init__(self):
        # Assign an attribute ".data" to all new instances of Order
        self.data = Olist().get_data()

    def get_wait_time(self, is_delivered=True):
        """
        Returns a DataFrame with:
        [order_id, wait_time, expected_wait_time, delay_vs_expected, order_status]
        and filters out non-delivered orders unless specified
        """
        # Hint: Within this instance method, you have access to the instance of the class Order in the variable self, as well as all its attributes
        orders = self.data['orders'].copy()

        if is_delivered:
            orders = orders[orders['order_status'] == 'delivered'].copy()

        orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
        orders['order_approved_at'] = pd.to_datetime(orders['order_approved_at'])
        orders['order_delivered_customer_date'] = pd.to_datetime(orders['order_delivered_customer_date'])
        orders['order_estimated_delivery_date'] = pd.to_datetime(orders['order_estimated_delivery_date'])
        orders['order_delivered_carrier_date'] = pd.to_datetime(orders['order_delivered_carrier_date'])

        one_day = pd.Timedelta(1, 'D')

        # wait_time: gerçek teslim - satın alma

        orders['wait_time'] = (orders['order_delivered_customer_date'] - orders['order_purchase_timestamp']) / one_day

        # expected_wait_time: tahmini teslim - satın alma

        orders['expected_wait_time'] = (orders['order_estimated_delivery_date'] - orders['order_purchase_timestamp']) / one_day


        # delay_vs_expected: gerçek teslim - tahmini teslim, sonra negatifleri 0'la

        orders['delay_vs_expected'] = ((orders['order_delivered_customer_date'] - orders['order_estimated_delivery_date']) / one_day).clip(lower=0)

        return orders[['order_id', 'wait_time', 'expected_wait_time',
                   'delay_vs_expected', 'order_status']]

    def get_review_score(self):
        """
        Returns a DataFrame with:
        order_id, dim_is_five_star, dim_is_one_star, review_score
        """
        reviews = self.data['order_reviews'].copy()
        reviews['dim_is_five_star'] = reviews['review_score'].apply(lambda x: 1 if x == 5 else 0)
        reviews['dim_is_one_star'] = reviews['review_score'].apply(lambda x: 1 if x == 1 else 0)
        return reviews[['order_id', 'dim_is_five_star', 'dim_is_one_star', 'review_score']]

    def get_number_items(self):
        """
        Returns a DataFrame with:
        order_id, number_of_items
        """
        items = self.data['order_items'].copy()
        number_of_items = items.groupby('order_id')['order_item_id'].count().reset_index()
        number_of_items.rename(columns={'order_item_id': 'number_of_items'}, inplace=True)
        return number_of_items

    def get_number_sellers(self):
        """
        Returns a DataFrame with:
        order_id, number_of_sellers
        """
        sellers = self.data['order_items'].copy()
        number_of_sellers = sellers.groupby('order_id')['seller_id'].nunique().reset_index()
        number_of_sellers.rename(columns={'seller_id': 'number_of_sellers'}, inplace=True)
        return number_of_sellers

    def get_price_and_freight(self):
        """
        Returns a DataFrame with:
        order_id, price, freight_value
        """
        price_freight = self.data['order_items'].copy()
        price_and_freight = price_freight.groupby('order_id')[['price', 'freight_value']].sum().reset_index()
        return price_and_freight

    # Optional
    def get_distance_seller_customer(self):
        """
        Returns a DataFrame with:
        order_id, distance_seller_customer
        """
        data = self.data

        # Posta kodu başına tek koordinat
        geo = data['geolocation'].copy()
        geo_unique = (geo.groupby('geolocation_zip_code_prefix', as_index=False)
                      .agg({'geolocation_lat': 'mean',
                            'geolocation_lng': 'mean'}))

        # Satıcı koordinatları (kalem düzeyinde)
        sellers_geo = (data['order_items'][['order_id', 'seller_id']]
                       .merge(data['sellers'], on='seller_id')
                       .merge(geo_unique,
                              left_on='seller_zip_code_prefix',
                              right_on='geolocation_zip_code_prefix'))

        # Müşteri koordinatları (sipariş düzeyinde)
        customers_geo = (data['orders'][['order_id', 'customer_id']]
                         .merge(data['customers'], on='customer_id')
                         .merge(geo_unique,
                                left_on='customer_zip_code_prefix',
                                right_on='geolocation_zip_code_prefix'))

        # İki tarafı buluştur
        matching_geo = sellers_geo.merge(customers_geo,
                                         on='order_id',
                                         suffixes=('_seller', '_customer'))

        # Satır satır haversine mesafesi
        matching_geo['distance_seller_customer'] = matching_geo.apply(
            lambda row: haversine_distance(row['geolocation_lat_seller'],
                                           row['geolocation_lng_seller'],
                                           row['geolocation_lat_customer'],
                                           row['geolocation_lng_customer']),
            axis=1)

        # Kalem düzeyi → sipariş düzeyi (ortalama)
        return (matching_geo
                .groupby('order_id', as_index=False)
                .agg({'distance_seller_customer': 'mean'}))

    def get_training_data(self,
                          is_delivered=True,
                          with_distance_seller_customer=False):
        """
        Returns a clean DataFrame (without NaN), with the all following columns:
        ['order_id', 'wait_time', 'expected_wait_time', 'delay_vs_expected',
        'order_status', 'dim_is_five_star', 'dim_is_one_star', 'review_score',
        'number_of_items', 'number_of_sellers', 'price', 'freight_value',
        'distance_seller_customer']
        """
        # Hint: make sure to re-use your instance methods defined above
        training = (self.get_wait_time(is_delivered)
                    .merge(self.get_review_score(), on='order_id')
                    .merge(self.get_number_items(), on='order_id')
                    .merge(self.get_number_sellers(), on='order_id')
                    .merge(self.get_price_and_freight(), on='order_id')
                    )
        
        return training.dropna()
