from src.database import Cepage, Cetaphil, Eucerin, Eximia
from src.database import Isdin, Loreal, Revlon, Vichy, LRP

# products from cepage brand
table_filepath = './database/tables/cepage.xlsx'
txt_folderpath = './database/txt/'
cepage = Cepage(filepath=table_filepath)
cepage.to_txt(folderpath=txt_folderpath)

# products from cetaphil brand
table_filepath = './database/tables/cetaphil.xlsx'
txt_folderpath = './database/txt/'
cetaphil = Cetaphil(filepath=table_filepath)
cetaphil.to_txt(folderpath=txt_folderpath)

# products from eucerin brand
table_filepath = './database/tables/eucerin.xlsx'
txt_folderpath = './database/txt/'
eucerin = Eucerin(filepath=table_filepath)
eucerin.to_txt(dataframe=eucerin.unify(), folderpath=txt_folderpath)

# products from eximia brand
table_filepath = './database/tables/eximia.xlsx'
txt_folderpath = './database/txt/'
eximia = Eximia(filepath=table_filepath)
eximia.to_txt(folderpath=txt_folderpath)

# products from isdin brand
table_filepath = './database/tables/isdin.xlsx'
txt_folderpath = './database/txt/'
isdin = Isdin(filepath=table_filepath)
isdin.to_txt(folderpath=txt_folderpath)

# products from loreal brand
table_filepath = './database/tables/loreal.xlsx'
txt_folderpath = './database/txt/'
loreal = Loreal(filepath=table_filepath, n_sheets=5)
loreal.to_txt(folderpath=txt_folderpath)

# products from revlon brand
table_filepath = './database/tables/revlon.xlsx'
txt_folderpath = './database/txt/'
revlon = Revlon(filepath=table_filepath, n_sheets=5)
revlon.to_txt(folderpath=txt_folderpath)

# products from vichy brand
table_filepath = './database/tables/vichy.xlsx'
txt_folderpath = './database/txt/'
vichy = Vichy(filepath=table_filepath)
vichy.to_txt(folderpath=txt_folderpath)

# products from la roche posay brand
table_filepath = './database/tables/lrp.xlsx'
txt_folderpath = './database/txt/'
lrp = LRP(filepath=table_filepath)
lrp.to_txt(folderpath=txt_folderpath)
