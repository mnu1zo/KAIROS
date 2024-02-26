import pandas as pd 
from sqlalchemy import create_engine

# Read the CSV file
df = pd.read_csv(r'D:\User\season\Desktop\hackerthon\building.csv')



# Create the connection
engine = create_engine('mysql+pymysql://root:ScE1234**@orion.mpokpo.ac.kr/BuildingMap')
df.to_sql('building',con=engine,if_exists='append',index=False)