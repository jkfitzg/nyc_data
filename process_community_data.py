import MySQLdb as mdb
import sys
import csv
import numpy as np
import pandas as pd
import string as s

  
def build_population_df():
    # Build pandas data frame of Population by Community District
    # Data from City of New York, 2010
    
    path = '/Users/jamie/GitHub/nyc_data/'
    
    # Declare empty data frame
    n_community_districts = 59
    indicies = range(n_community_districts)
    columns = ['Borough','Community num', 'Community name', 'Population']
    Population_by_Community_df = pd.DataFrame(index=indicies,columns=columns)
    
    # Open file,load data into the data frame
    o = open(path+'nyc population by community district.csv','rU')
    csv_data = csv.reader(o)

    for i in range(n_community_districts):
        Population_by_Community_df.ix[i,:] = csv_data.next()
        Population_by_Community_df.ix[i,'Community num'] = \
            Population_by_Community_df.ix[i,'Community num'].strip() #remove extra spaces
    
        Population_by_Community_df.ix[i,'Population'] = \
            int(Population_by_Community_df.ix[i,'Population'].replace(",", ""))
    
    return Population_by_Community_df
    
def build_zip_to_community_df():
    # Build pandas data frame of Zip code to Community District mapping
    # Approximate mapping by Frank Donnelly, Geospatial Data Librarian, Baruch College CUNY
    # Source: http://guides.newman.baruch.cuny.edu/ld.php?content_id=7154885
    
    path = '/Users/jamie/GitHub/nyc_data/'
    # Open file, look at column names
    o = open(path+'nyc zip to community district.csv','rU')
    csv_data = csv.reader(o)
    file_col_names = csv_data.next()
    # print file_col_names

    # Declare empty data frame
    n_zips = 211
    indicies = range(n_zips)
    columns = ['Zip','PUMA num', 'Community name long', 'Community name short','Per in Com','Per of Com']
    Zip_to_community_mapping_df = pd.DataFrame(index=indicies,columns=columns)
    
    for i in range(n_zips):
        Zip_to_community_mapping_df.ix[i,:] = csv_data.next()
    return Zip_to_community_mapping_df
    
def parse_long_community_name(long_name):
    # Return borough, district numbers, short name
    # assumes the format "NYC--<Borough> Community District <n OR number n1 & n2>--<short name>"
    name_halfs = s.split(long_name,'--')
    short_name = name_halfs[1]  #short name is following '--'
    
    # get borough and numbers
    first_half = name_halfs[0]
    split_first_half = first_half.split('Community District')
    borough = split_first_half[0].split('NYC-')[1].strip()

    # now get one or more numbers
    numbers = split_first_half[1].split('&')
    numbers_array = [n.split()[0] for n in numbers]
    
    return short_name, borough, numbers_array
    
def merge_nyc_community_info(Zip_to_community_mapping_df,Population_by_Community_df):
    # Now combine the useful data from these two sources
    # to build a data frame of Community names, Boroughs, ZIP codes, Population 
    # then for each community I can rank the noise complaints per capita and look 
    # at the types of noise/community district
    
    unique_communities = Zip_to_community_mapping_df['Community name long'].unique()
    
    n_communities = np.size(unique_communities) 
                    #some communities are merged here, so the count differs from other df
                    
    # Build my community df and community zip codes dictionary
    indicies = range(n_communities)
    columns = ['Borough','Num 1','Num 2','Community name','Population']
    NYC_Community_df = pd.DataFrame(index=indicies,columns=columns)

    NYC_Community_zips_dict = {}
    
    for i in range(n_communities):
        # parse the long community names to get the short names, boroughs, and bourough numbers
        this_long_name = unique_communities[i]
    
        short_name, borough, numbers_array = parse_long_community_name(this_long_name)
        NYC_Community_df.ix[i,'Community name'] = short_name
        NYC_Community_df.ix[i,'Borough'] = borough
        NYC_Community_df.ix[i,'Num 1'] = numbers_array[0]
        if len(numbers_array) == 2:  #for merged community numbers
            NYC_Community_df.ix[i,'Num 2'] = numbers_array[1]
    
        # Now add the populations. Some communities combine two districts
        this_borough_i = np.where(Population_by_Community_df['Borough'] == borough)[0]
        this_num_i = np.where(Population_by_Community_df['Community num'] == numbers_array[0])[0]
        if len(numbers_array) == 2:
            this_num2_i = np.where(Population_by_Community_df['Community num'] == numbers_array[1])[0]
            this_num_i = np.union1d(this_num_i,this_num2_i)
        this_pop_i = np.intersect1d(this_borough_i,this_num_i)
    
        NYC_Community_df.ix[i,'Population'] = Population_by_Community_df.ix[this_pop_i[0],'Population']
        if len(numbers_array) == 2:
            NYC_Community_df.ix[i,'Population'] = NYC_Community_df.ix[i,'Population'] +\
                Population_by_Community_df.ix[this_pop_i[1],'Population']
    
        #build a dictionary of short_name: zip codes
        community_is = Zip_to_community_mapping_df['Community name short'] == short_name
        community_zips_list = Zip_to_community_mapping_df.ix[community_is,'Zip'].values.tolist()
        NYC_Community_zips_dict[short_name] = tuple(community_zips_list)
        
    return NYC_Community_df, NYC_Community_zips_dict
    