import sys, os, re
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(os.path.abspath(os.path.join('..', 'src')))

# Global variables
bullets = ['\u2022', '\u00B7', '\u25CF', '\u23FA', '\u26AB', 
           '\u2B24', '\u2219', '\u22C5', '\u1F311', '\u30FB']
pattern = f"[{re.escape(''.join(bullets))}]"

# Global functions
def get_engine(file_path:str):
    if file_path.endswith('.xlsx'):
        return 'openpyxl'
    elif file_path.endswith('.xls'):
        return 'xlrd'
    else:
        return None

def reduce_strings(strings):
    # Reduce strings to unique strings, ignoring case but returning original case
    unique_strings = []
    lower_to_original = {}
    
    # Sort by length, descending
    strings.sort(key=len, reverse=True)
    
    for string in strings:
        stripped_string = string.strip()
        string_lower = stripped_string.lower()
        
        if not any(string_lower in unique.lower() for unique in unique_strings):
            unique_strings.append(stripped_string)
            lower_to_original[string_lower] = stripped_string
            
    # Return unique strings respecting original case
    return [lower_to_original[unique.lower()] for unique in unique_strings]

def unify(strings:list):
    # unify strings that are similar
    filter_strings = []
    unique_strings = []
    
    for i in range(len(strings)):
        is_sub = False
        for j in range(len(strings)):
            if (i!=j) and (strings[i] in strings[j]):
                is_sub = True
                break
        if not is_sub:
            filter_strings.append(strings[i])
    
    for s in filter_strings:
        if s not in unique_strings:
            unique_strings.append(s)
    
    return unique_strings

def remove(strings:list, to_remove:str, all:bool=False):
    # remove all strings that are equal to to_remove
    to_remove = to_remove.lower().strip()
    lowercase = [s.lower().strip() for s in strings]
    idx_to_remove = [i for i, s in enumerate(lowercase) if s == to_remove]
    new_strings = [s.strip() for i, s in enumerate(strings) if i not in idx_to_remove]
    if all:
        new_strings = [s.replace(to_remove, '').strip() for s in new_strings]
        new_strings = [s.replace(to_remove.capitalize(), '').strip() for s in new_strings]
        new_strings = [s.replace(to_remove.upper(), '').strip() for s in new_strings]

    return new_strings

def squash(strings:list):
    pattern_units = [r'(\d+)\s*([a-zA-Z]+)', r'\1\2']
    return re.sub(pattern_units[0], pattern_units[1], strings)

def check_string(string, numeric=False):
    # If 'string' is a mix of letters and numbers, return True
    # Note: Whitespaces are not allowed
    if numeric:
        # check if it is only numbers
        return bool(re.match(r'^\d+$', string))
    else:
        return bool(re.match(r'^\w+$', string))
    
def clear_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df.dropna(how='all', inplace=True)          # delete empty rows
    #df.dropna(axis=1, how='all', inplace=True)  # delete empty columns
    df.drop_duplicates(inplace=True)            # delete duplicates
    for column in df.columns:
        if df[column].dtype in [int, float]:
            df[column] = df[column].map(lambda x: str(int(float(x))) if not pd.isna(x) else str(x))
            df[column] = df[column].map(lambda s: squash(s.replace('nan', '')))
        else:
            df[column] = df[column].map(str)
            df[column] = df[column].map(lambda x: x.strip())                                                            # strip whitespaces at the beginning and end
            df[column] = df[column].map(lambda x: re.split(r'\n|\s{2,}', x))                                            # split by new line or many spaces
            df[column] = df[column].map(lambda s: [squash(x.strip()) for x in s] if s != '' else s)                     # squash strings
            df[column] = df[column].map(lambda s: [x.replace('nan', '') for x in s])
            df[column] = df[column].map(lambda s: [x for x in s if x != ''])                                            # remove empty strings
            df[column] = df[column].map(lambda s: '. '.join(s)+'.' if (s!='') or (not check_string(s, True)) else s)    # join strings with '.'
            df[column] = df[column].map(lambda s: re.sub(r'\.{2,}', '.', s))                                            # remove multiple dots
            df[column] = df[column].map(lambda s: re.sub(r'\s+', ' ', s))                                               # replace multiple spaces with one space
            df[column] = df[column].map(lambda s: re.sub(pattern, '', s))                                               # delete symbols from pattern list
            df[column] = df[column].map(lambda s: s.replace('.', ''))
    return df

def make_keywords(strings:list) -> str:
    strings = [s for s in strings if s]
    keywords = []
    for string in strings:
        keywords += re.split(r'[;,|/.-]', string)
    keywords = [re.sub(r'^[^\w]+|[^\w]+$', '', kws) for kws in keywords]    # remove punctuation (begin, end)
    keywords = [kws.strip().lower() for kws in keywords]                    # remove whitespaces and lowercase
    keywords = reduce_strings(keywords)                                     # unify strings, remove duplicates
    keywords = '; '.join(keywords) + '.'                                    # join keywords by ;
    keywords = '' if keywords=='.' else keywords
    return keywords

def reduce_dots(string: str) -> str:
    string = re.sub(r'\.{2,}', '.', string)
    string = re.sub(r'\.\s*\.\s*\.\s*', '. ', string)
    return string

def simple_join(strings: list, reduce:bool=False) -> str:
    strings = reduce_strings(strings) if reduce else strings
    strings = [s for s in strings if s]
    if strings: 
        strings = '. '.join(strings) + '.'
        strings = re.sub(r'\.{2,}', '.', strings)
        strings = re.sub(r'\.\s*\.\s*\.\s*', '. ', strings)
        return strings
    else:
        return ''

def many_lines_join(string: str) -> str:
    string_list = re.split(r'\n|\s{2,}', string)                                        # split by new line or many spaces
    string_list = [s for s in string_list if s]                                         # remove empty strings
    string_list = [s.strip()+'.' if not s.endswith('.') else s for s in string_list]    # add end dot
    string = ' '.join(string_list)                                                      # join strings
    string = re.sub(r'\.{2,}', '.', string)
    string = re.sub(r'\.\s*\.\s*\.\s*', '. ', string)

class Cepage(object):
    BRAND_LOWER = 'cepage'
    BRAND_UPPER = 'CEPAGE'
    BRAND_CAP = 'Cepage'
    columns = ["categoria", "nombre de linea", "tipo de linea", "necesidades", "sku", 
               "ean", "producto", "descripcion", "indicacion", "uso", "inci", "activos", 
               "beneficios", "generales", "presentacion", "ancho", "profundidad", "alto", "peso"]
    
    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.df = pd.read_excel(filepath, engine=get_engine(filepath))
        self.df.columns = Cepage.columns    # rename columns
        self.df = clear_dataframe(self.df)  # clean dataframe

        # Get some parameters
        self.n_samples = self.df.shape[0]
        self.n_features = self.df.shape[1]
        self.n_words = self.df.map(lambda x: len(x.split(' '))).sum().sum()
        self.n_chars = self.df.map(lambda x: len(x)).sum().sum()

    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        df = self.df.copy()
        
        name = df['producto']
        name = name.apply(lambda s: f"Producto {s}. Marca {Cepage.BRAND_CAP}.")

        code = df[['ean', 'sku']]
        code = code.apply(lambda row: row.to_list(), axis=1)
        code = code.apply(lambda s: f"Código EAN {s[0]}. Código SKU {s[1]}.")

        features = df[['descripcion', 'indicacion', 'uso', 'beneficios']]
        features = features.apply(lambda row: row.to_list(), axis=1)
        features = features.apply(lambda s: f"Descripción: {s[0]}. Indicaciones: {s[1]}. Uso: {s[2]}. Beneficios: {s[3]}.")
        features = features.apply(lambda s: reduce_dots(s))

        keywords = df[['categoria', 'nombre de linea', 'tipo de linea', 'necesidades', 'generales']]
        keywords = keywords.apply(lambda row: row.to_list(), axis=1)
        keywords = keywords.apply(lambda kws: make_keywords(kws))
        keywords = keywords.apply(lambda kws: f"Keywords: {kws}")

        dims = df[['ancho', 'profundidad', 'alto']]
        dims = dims.apply(lambda row: row.to_list(), axis=1)
        dims = dims.apply(lambda dim: f"Dimensiones {dim[0]}mm x {dim[1]}mm x {dim[2]}mm." if any(dim) else '')

        features = pd.DataFrame(data={0:features, 1:keywords, 2:df['presentacion'], 3:dims, 4:df['peso']})
        features = features.apply(lambda row: row.to_list(), axis=1)
        features = features.to_list()
        features_kustom = []
        for feature in features:
            s = ''
            s += f"{feature[0]}. " if feature[0] else ''
            s += f"{feature[1]}. " if feature[1] else ''
            s += f"Presentación {feature[2]}. " if feature[2] else ''
            s += f"{feature[3]}. " if feature[3] else ''
            s += f"Peso {feature[4]}gr." if feature[4] else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))
        
        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        code.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
        dataframe = dataframe.map(lambda s: reduce_dots(s))

        return dataframe

    def to_txt(self, folderpath: str='../data/txt/bybrand/cepage/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = Cepage.BRAND_LOWER
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()
    
    def to_sql(self, dbname:str, tablename:str):
        df = self.unify()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)


class Cetaphil(object):
    BRAND_LOWER = 'cetaphil'
    BRAND_UPPER = 'CETAPHIL'
    BRAND_CAP = 'Cetaphil'
    columns = ["producto", "marca", "nombre", "presentacion", "ean", 
               "categoria", "subcategoria", "zona", "descripcion", "keywords"]
    columns_to_removed = ["producto", "marca"]
    
    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.df = pd.read_excel(filepath, engine=get_engine(filepath))
        self.df.columns = Cetaphil.columns                              # rename columns
        self.df.drop(columns=Cetaphil.columns_to_removed, inplace=True) # remove some columns
        self.df = clear_dataframe(self.df)                              # clean dataframe

        # Get some parameters
        self.n_samples = self.df.shape[0]
        self.n_features = self.df.shape[1]
        self.n_words = self.df.map(lambda x: len(x.split(' '))).sum().sum()
        self.n_chars = self.df.map(lambda x: len(x)).sum().sum()
    
    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        df = self.df.copy()

        name = df['nombre']
        name = name.apply(lambda s: f"Producto {s}. Marca {Cetaphil.BRAND_CAP}.")

        code = df['ean']
        code = code.apply(lambda s: f"Código EAN {s}.")

        keywords = df[['categoria', 'subcategoria', 'zona', 'keywords']]
        keywords = keywords.apply(lambda row: row.to_list(), axis=1)
        keywords = keywords.apply(lambda kws: make_keywords(kws))

        features = pd.DataFrame(data={0:df['descripcion'], 1:keywords, 2:df['presentacion']})
        features = features.apply(lambda row: row.to_list(), axis=1)
        features = features.to_list()
        features_kustom = []
        for feature in features:
            s = ''
            s += f"Descripción: {feature[0]}. " if feature[0] else ''
            s += f"Keywords: {feature[1]}. " if feature[1] else ''
            s += f"Presentación {feature[2]}. " if feature[2] else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))

        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        code.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
        dataframe = dataframe.map(lambda s: reduce_dots(s))

        return dataframe

    def to_txt(self, folderpath: str='../data/txt/bybrand/cetaphil/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = Cetaphil.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()
    
    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)


class Eucerin(object):
    BRAND_LOWER = 'eucerin'
    BRAND_UPPER = 'EUCERIN'
    BRAND_CAP = 'Eucerin'
    columns = ["fecha", "estado", "ean", "producto", "linea", "categoria",
               "segmento", "contenido", "zona", "nombre", "nombre corto",
               "descripcion", "descripcion corta", "beneficios 1", "beneficios 2",
               "beneficios 3", "beneficios 4", "beneficios 5", "piel", "propiedades",
               "ingredientes", "uso", "keywords"]
    columns_to_removed = ["fecha", "estado"]
    
    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.df = pd.read_excel(filepath, engine=get_engine(filepath))
        self.df.columns = Eucerin.columns                               # rename columns
        self.df.drop(columns=Eucerin.columns_to_removed, inplace=True)  # remove some columns
        self.df = clear_dataframe(self.df)                              # clean dataframe

        # Get some parameters
        self.n_samples = self.df.shape[0]
        self.n_features = self.df.shape[1]
        self.n_words = self.df.map(lambda x: len(x.split(' '))).sum().sum()
        self.n_chars = self.df.map(lambda x: len(x)).sum().sum()

    def unify_simple(self) -> pd.DataFrame:

        df = self.df.copy()

        # Build name field
        name = df['producto']
        name = name.apply(lambda s: f"Producto {s}. Marca {Eucerin.BRAND_CAP}.")

        # Build features field
        benefits = df[[f"beneficios {i}" for i in range(1,6)]]
        benefits = benefits.apply(lambda row: row.to_list(), axis=1)
        benefits = benefits.apply(lambda s: simple_join(s))

        use = df['uso'].apply(lambda x: x.replace('\n', '. '))
        use = use.apply(lambda s: reduce_dots(s))

        ft_dict = {0:df['descripcion'], 1:df['contenido'], 2:df['propiedades'], 3:benefits, 4:use}
        features = pd.DataFrame(data=ft_dict)
        features = features.apply(lambda row: row.to_list(), axis=1)
        features = features.to_list()
        features_kustom = []
        for feature in features:
            s = ''
            s += f"Descripción: {feature[0]}. " if feature[0] else ''
            s += f"Presentación {feature[1]}. " if feature[1] else ''
            s += f"Propiedades: {feature[2]}. " if feature[2] else ''
            s += f"Beneficios: {feature[3]}. " if feature[3] else ''
            s += f"Modo de uso: {feature[4]}. " if feature[4] else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))

        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Descripción':features})
        dataframe = dataframe.map(lambda s: reduce_dots(s))

        return dataframe
    
    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        df = self.df.copy()

        # Build name field
        name = df['producto']
        name = name.apply(lambda s: f"Producto {s}. Marca {Eucerin.BRAND_CAP}.")

        # Build code field
        code = df['ean']
        code = code.apply(lambda s: f"Código EAN {s}.")
        
        # Build features field
        keywords = df[['linea', 'categoria', 'segmento', 'zona', 'piel', 'keywords']]
        keywords = keywords.apply(lambda row: row.to_list(), axis=1)
        keywords = keywords.apply(lambda kws: make_keywords(kws))

        benefits = df[[f"beneficios {i}" for i in range(1,6)]]
        benefits = benefits.apply(lambda row: row.to_list(), axis=1)
        benefits = benefits.apply(lambda s: simple_join(s))

        use = df['uso'].apply(lambda x: x.replace('\n', '. '))
        use = use.apply(lambda s: reduce_dots(s))

        ft_dict = {0:df['descripcion'], 1:df['contenido'], 2:df['propiedades'], 3:benefits, 4:use, 5:keywords}
        features = pd.DataFrame(data=ft_dict)
        features = features.apply(lambda row: row.to_list(), axis=1)
        features = features.to_list()
        features_kustom = []
        for feature in features:
            s = ''
            s += f"Descripción: {feature[0]}. " if feature[0] else ''
            s += f"Contenido: {feature[1]}. " if feature[1] else ''
            s += f"Propiedades: {feature[2]}. " if feature[2] else ''
            s += f"Beneficios: {feature[3]}. " if feature[3] else ''
            s += f"Modo de uso: {feature[4]}. " if feature[4] else ''
            s += f"Keywords: {feature[5]}. " if feature[5] else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))

        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        code.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
        dataframe = dataframe.map(lambda s: reduce_dots(s))

        return dataframe
    
    def to_txt(self, dataframe, folderpath: str='../data/txt/bybrand/eucerin/', separate: bool=False) -> None:
        lines = [' '.join(list(row[1].values)) for row in dataframe.iterrows()]
        brand = Eucerin.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()

    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)


class Eximia(object):
    BRAND_LOWER = 'eximia'
    BRAND_UPPER = 'EXIMIA'
    BRAND_CAP = 'Eximia'
    columns = ["ean", "nombre", "necesidad", "linea", "piel", "titulo", 
               "bajada", "descripcion", "uso", "activos", "beneficios", 
               "comentarios", "inci", "keywords", "presentacion", "contenido", 
               "unidades", "ancho", "profundidad", "alto", "peso"]

    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.df = pd.read_excel(filepath, engine=get_engine(filepath))

        self.df = self.df.iloc[1:]          # delete the first row (wrong headers)
        self.df.columns = Eximia.columns    # rename columns
        self.df = clear_dataframe(self.df)  # clean dataframe

        # Get some parameters
        self.n_samples = self.df.shape[0]
        self.n_features = self.df.shape[1]
        self.n_words = self.df.map(lambda x: len(x.split(' '))).sum().sum()
        self.n_chars = self.df.map(lambda x: len(x)).sum().sum()

    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        df = self.df.copy()

        # Build name field
        name = df['nombre']
        name = name.apply(lambda s: f"Producto {s}. Marca {Eximia.BRAND_CAP}.")
        name = name.apply(lambda s: reduce_dots(s))

        # Build code field
        code = df['ean']
        code = code.apply(lambda s: f"Código EAN {s}.")
        code = code.apply(lambda s: reduce_dots(s))

        # Build features field
        keywords = df[['necesidad', 'linea', 'piel', 'keywords']]
        keywords = keywords.apply(lambda row: row.to_list(), axis=1)
        keywords = keywords.apply(lambda kws: make_keywords(kws))

        df['ancho'] = df['ancho'].apply(lambda x: x+'mm' if x!='' else x)
        df['profundidad'] = df['profundidad'].apply(lambda x: x+'mm' if x!='' else x)
        df['alto'] = df['alto'].apply(lambda x: x+'mm' if x!='' else x)
        df['peso'] = df['peso'].apply(lambda x: x+'gr' if x!='' else x)

        presentation = df[['presentacion', 'contenido', 'unidades']]
        presentation = presentation.apply(lambda row: row.to_list(), axis=1)
        presentation = presentation.apply(lambda row: squash(' '.join(row)))
        presentation = presentation.apply(lambda row: row if (row.endswith('.') or row=='') else row+'.')

        dims = df[['ancho', 'profundidad', 'alto']]
        dims = dims.apply(lambda row: row.to_list(), axis=1)
        dims = dims.apply(lambda row: ' x '.join(row) if all([r!='' for r in row]) else '')

        features = df[['titulo', 'bajada', 'descripcion', 'uso', 'activos', 'beneficios', 'comentarios', 'inci']]
        features = features.apply(lambda row: row.to_list(), axis=1)
        features = features.apply(lambda row: simple_join(row))

        features_kustom = []
        for ft, kws, ppt, dim, weight in zip(features, keywords, presentation, dims, df['peso']):
            s = ''
            s += f"Descripción: {ft}. " if ft else ''
            s += f"Keywords: {kws}. " if kws else ''
            s += f"Presentación: {ppt}. " if ppt else ''
            s += f"Dimensiones {dim}. " if dim else ''
            s += f"Peso {weight}." if weight else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))

        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        code.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
        dataframe = dataframe.map(str)
        dataframe = dataframe.apply(lambda s: s.replace('nan', ''))

        return dataframe

    def to_txt(self, folderpath: str='../data/txt/bybrand/eximia/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = Eximia.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()
    
    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)

class Isdin(object):
    BRAND_LOWER = 'isdin'
    BRAND_UPPER = 'ISDIN'
    BRAND_CAP = 'Isdin'
    columns = ["id", "codigo", "sku", "ean", "nombre", "variante", 
               "marca", "generales", "id_ml", "descripcion"]
    columns_to_drop = ["id_ml"]

    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.df = pd.read_excel(filepath, engine=get_engine(filepath))  # read data
        self.df = self.df.iloc[1:]                                      # delete the first row (wrong headers)
        self.df.columns = Isdin.columns                                 # rename columns
        self.df = self.df.drop(columns=Isdin.columns_to_drop)
        self.df = clear_dataframe(self.df)                              # clean dataframe

        # Get some parameters
        self.n_samples = self.df.shape[0]
        self.n_features = self.df.shape[1]
        self.n_words = self.df.map(lambda x: len(x.split(' '))).sum().sum()
        self.n_chars = self.df.map(lambda x: len(x)).sum().sum()

    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        df = self.df.copy()

        # Build name field
        name = df['nombre']
        name = name.apply(lambda s: f"Producto {s}. Marca {Isdin.BRAND_CAP}." if s else f"Marca {Isdin.BRAND_CAP}.")
        name = name.apply(lambda s: reduce_dots(s))

        # Build code field
        code = df[['id', 'codigo', 'sku', 'ean']]
        code = code.apply(lambda row: row.to_list(), axis=1)
        code_kustom = []
        for row in code:
            s = ''
            s += f"Id {row[0]}. " if row[0] else ''
            s += f"Código {row[1]}. " if row[1] else ''
            s += f"Código SKU {row[2]}. " if row[2] else ''
            s += f"Código EAN {row[3]}." if row[3] else ''
            code_kustom.append(s)
        code = pd.Series(code_kustom)
        code = code.apply(lambda s: reduce_dots(s))

        features = df[['descripcion', 'generales', 'variante']]
        features = features.apply(lambda row: row.to_list(), axis=1)
        features_kustom = []
        for row in features:
            s = ''
            s += f"Descripción: {row[0]}. " if row[0] else ''
            s += f"{row[1]}. " if row[1] else ''
            s += f"{row[2]}." if row[2] else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))

        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        code.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
        dataframe = dataframe.map(str)
        dataframe = dataframe.apply(lambda s: s.replace('nan', ''))

        return dataframe
    
    def to_txt(self, folderpath: str='../data/txt/bybrand/isdin/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = Isdin.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()

    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)


class Loreal(object):
    BRAND_LOWER = 'loreal'
    BRAND_UPPER = 'LOREAL'
    BRAND_CAP = 'Loreal'
    columns = {0:["categoria", "marca", "franquicia", "subfranquicia", "ean", "titulo", 
              "tipo", "descripcion", "beneficios", "aplicacion", "piel", "uso", "zona", "efecto", 
              "hipoalergenico", "crosselling", "keywords", "tamaño", "unidades", "link", "0", "1"], 
           1:["categoria", "marca", "franquicia", "subfranquicia", "ean", "titulo", 
              "tipo", "descripcion", "beneficios", "aplicacion", "crosselling", "keywords", 
              "hipoalergenico", "pelo", "uso", "tamaño", "unidades", "link", "0"], 
           2:["categoria", "marca", "franquicia", "subfranquicia", "ean", "titulo", "color", 
              "numero", "nombre", "tipo de producto", "descripcion", "presentacion", "beneficios", 
              "aplicacion", "crosselling", "keywords", "hipoalergenico", "tamaño", "unidades", "link"],
           3:["categoria", "ean", "marca", "franquicia", "subfranquicia", "titulo", "tipo de producto", 
              "resumen", "descripcion", "adicionales", "presentacion", "beneficio 1", "beneficio 2", 
              "beneficio 3", "aplicacion", "crosselling", "keywords", "hipoalergenico", "piel", "uso", 
              "zona", "efecto", "codigo hexa", "tamaño", "unidades"],
           4:["categoria", "marca", "ean", "franquicia", "subfranquicia", "zona", "titulo", 
              "color", "numero", "nombre", "tipo de producto", "descripcion", "beneficios", 
              "aplicacion", "piel", "uso", "efecto", "hipoalergenico", "crosselling", "keywords", 
              "tamaño", "unidades", "link"]}
    columns_to_drop = {0:["crosselling", "link", "0", "1"], 
                    1:["crosselling", "link", "0"],
                    2:["color", "numero", "nombre", "crosselling", "link"],
                    3:["efecto", "codigo hexa"],
                    4:["color", "numero", "nombre", "crosselling", "link"]}

    def __init__(self, filepath:str, n_sheets) -> None:
        self.filepath = filepath
        self.n_sheets = n_sheets
        self.df_list = []
        for i in range(n_sheets):
            df = pd.read_excel(filepath, sheet_name=i, engine=get_engine(filepath))
            df.columns = Loreal.columns[i]
            df.drop(columns=Loreal.columns_to_drop[i], inplace=True)
            df = clear_dataframe(df)
            self.df_list.append(df)

        # Get some parameters
        self.n_samples = [df.shape[0] for df in self.df_list]
        self.n_features = [df.shape[1] for df in self.df_list]
        self.n_words = [df.map(lambda x: len(x.split(' '))).sum().sum() for df in self.df_list]
        self.n_chars = [df.map(lambda x: len(x)).sum().sum() for df in self.df_list]

    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        dataframes = []

        for i, df_i in enumerate(self.df_list):
            df = df_i.copy()

            # Build name field
            name = df[['marca', 'titulo']]
            name = name.apply(lambda row: row.to_list(), axis=1)
            name_kustom = []
            for row in name:
                s = ''
                s += f"Marca {row[0]}. " if row[0] else ''
                s += f"Título: {row[1]}." if row[1] else ''
                name_kustom.append(s)
            name = pd.Series(name_kustom)
            name = name.apply(lambda s: reduce_dots(s))

            # Build code field
            code = df['ean']
            code = code.apply(lambda s: f"Código EAN {s}." if s else '')
            code = code.apply(lambda s: reduce_dots(s))

            # Build features field
            keywords = df['keywords']
            keywords = keywords.apply(lambda kws: make_keywords([kws]))
            keywords = keywords.apply(lambda s: reduce_dots(s))
            keywords = keywords.apply(lambda s: f"Keywords: {s}" if s else '')

            presentation = df[["tamaño", "unidades"]]
            presentation = presentation.apply(lambda row: row.to_list(), axis=1)
            presentation_kustom = []
            for row in presentation:
                if row[0] and row[1]:
                    s = f"Presentación {row[0]}{row[1]}."
                else:
                    s = ''
                presentation_kustom.append(s)
            presentation = pd.Series(presentation_kustom)
            presentation = presentation.apply(lambda s: reduce_dots(s))

            no_features_columns = ["marca", "titulo", "ean", "tamaño", "unidades", "keywords", "tamaño", "unidades"]
            features_columns = [col for col in Loreal.columns[i] 
                                if col not in no_features_columns and 
                                col not in Loreal.columns_to_drop[i]]
            features = df[features_columns]
            features = features.apply(lambda row: row.to_list(), axis=1)
            features_kustom = []
            for fts, ppt, kws in zip(features, presentation, keywords):
                s = ''
                for i, column_name in enumerate(features_columns):
                    s += f"{column_name.capitalize()}: {fts[i]}. " if fts[i] else ''
                s += f"{ppt} " if ppt else ''
                s += f"{kws}" if kws else ''
                features_kustom.append(s)
            features = pd.Series(features_kustom)
            features = features.apply(lambda s: reduce_dots(s))

            # Reset index before building dataframe
            name.reset_index(drop=True, inplace=True)
            code.reset_index(drop=True, inplace=True)
            features.reset_index(drop=True, inplace=True)
            # Build unify dataframe
            dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
            dataframe = dataframe.map(str)
            dataframe = dataframe.apply(lambda s: s.replace('nan', ''))
            dataframes.append(dataframe)
        
        # Concatenate dataframes
        main_df = pd.concat(dataframes, ignore_index=True)
        condition = (main_df['Producto']=='') & (main_df['Código']=='')
        main_df = main_df[~condition]

        return main_df

    def to_txt(self, folderpath: str='../data/txt/bybrand/loreal/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = Loreal.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()

    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)


class Revlon(object):
    BRAND_LOWER = 'revlon'
    BRAND_UPPER = 'REVLON'
    BRAND_CAP = 'Revlon'
    columns = {0:["tipo", "categoria", "subcategoria", "familia", "product", "producto", "descripcion mkt", 
                  "caracteristicas", "codigo sap", "ean", "merch code", "tono", "stock"], 
               1:["tipo", "categoria", "subcategoria", "familia", "product", "producto", "descripcion mkt", 
                  "caracteristicas", "codigo sap", "ean", "merch code", "tono", "stock"], 
               2:["tipo", "categoria", "subcategoria", "familia", "product", "producto", "descripcion mkt", 
                  "caracteristicas", "codigo sap", "ean", "merch code", "stock"],
               3:["tipo", "categoria", "subcategoria", "familia", "product", "producto", "descripcion mkt", 
                  "caracteristicas", "codigo sap", "ean", "merch code", "tono", "stock"],
              4:["tipo", "categoria", "subcategoria", "familia", "product", "producto", "descripcion mkt", 
                 "caracteristicas", "codigo sap", "ean", "stock"]}
    columns_to_drop = ["stock"]

    def __init__(self, filepath:str, n_sheets) -> None:
        self.filepath = filepath
        self.n_sheets = n_sheets
        self.df_list = []
        for i in range(n_sheets):
            df = pd.read_excel(filepath, sheet_name=i, engine=get_engine(filepath))
            df.columns = Revlon.columns[i]
            df.drop(columns=Revlon.columns_to_drop, inplace=True)
            df = clear_dataframe(df)
            self.df_list.append(df)

        # Get some parameters
        self.n_samples = [df.shape[0] for df in self.df_list]
        self.n_features = [df.shape[1] for df in self.df_list]
        self.n_words = [df.map(lambda x: len(x.split(' '))).sum().sum() for df in self.df_list]
        self.n_chars = [df.map(lambda x: len(x)).sum().sum() for df in self.df_list]

    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        dataframes = []

        for i, df_i in enumerate(self.df_list):
            df = df_i.copy()
            
            # Build name field
            name = df[["product", "producto"]]
            name = name.apply(lambda row: row.to_list(), axis=1)
            name_kustom = []
            for row in name:
                s = ''
                s += f"Marca {Revlon.BRAND_CAP}. "
                s += f"Product {row[0]}. " if row[0] else ''
                s += f"Producto {row[1]}." if row[1] else ''
                name_kustom.append(s)
            name = pd.Series(name_kustom)
            name = name.apply(lambda s: reduce_dots(s))

            # Build code field
            code_columns = ["codigo sap", "ean"]
            code_columns += ["merch code"] if "merch code" in Revlon.columns[i] else []
            code = df[code_columns]
            code = code.apply(lambda row: row.to_list(), axis=1)
            code_kustom = []
            for row in code:
                s = ''
                s += f"Código SAP {row[0]}. " if row[0] else ''
                s += f"Código EAN {row[1]}. " if row[1] else ''
                if "merch code" in Revlon.columns[i]:
                    s += f"Merch code {row[2]}." if row[2] else ''
                code_kustom.append(s)
            code = pd.Series(code_kustom)
            code = code.apply(lambda s: reduce_dots(s))

            # Build features field
            no_features_columns = ["product", "producto", "codigo sap", "ean"]
            no_features_columns += ["merch code"] if "merch code" in Revlon.columns[i] else []
            features_columns = [col for col in Revlon.columns[i] 
                                if col not in no_features_columns and 
                                col not in Revlon.columns_to_drop]
            features = df[features_columns]
            features = features.apply(lambda row: row.to_list(), axis=1)
            features_kustom = []
            for fts in features:
                s = ''
                for i, column_name in enumerate(features_columns):
                    s += f"{column_name.capitalize()}: {fts[i]}. " if fts[i] else ''
                features_kustom.append(s)
            features = pd.Series(features_kustom)
            features = features.apply(lambda s: reduce_dots(s))

            # Reset index before building dataframe
            name.reset_index(drop=True, inplace=True)
            code.reset_index(drop=True, inplace=True)
            features.reset_index(drop=True, inplace=True)
            # Build unify dataframe
            dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
            dataframe = dataframe.map(str)
            dataframe = dataframe.apply(lambda s: s.replace('nan', ''))
            dataframes.append(dataframe)

        # Concatenate dataframes
        main_df = pd.concat(dataframes, ignore_index=True)
        condition = (main_df['Producto']=='') & (main_df['Código']=='')
        main_df = main_df[~condition]

        return main_df
    
    def to_txt(self, folderpath: str='../data/txt/bybrand/revlon/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = Revlon.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()

    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)


class Vichy(object):
    BRAND_LOWER = 'vichy'
    BRAND_UPPER = 'VICHY'
    BRAND_CAP = 'Vichy'
    columns = ["codigo", "sku", "ean", "producto", "uso", "marca", "ml_code", "descripcion"]
    columns_to_drop = ["ml_code"]

    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.df = pd.read_excel(filepath, engine=get_engine(filepath))
        self.df.columns = Vichy.columns
        self.df.drop(columns=Vichy.columns_to_drop, inplace=True)
        self.df = clear_dataframe(self.df)

        # Get some parameters
        self.n_samples = self.df.shape[0]
        self.n_features = self.df.shape[1]
        self.n_words = self.df.map(lambda x: len(x.split(' '))).sum().sum()
        self.n_chars = self.df.map(lambda x: len(x)).sum().sum()

    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        df = self.df.copy()
        
        # Build name field
        name = df[["producto", "marca"]]
        name = name.apply(lambda row: row.to_list(), axis=1)
        name_kustom = []
        for row in name:
            s = ''
            s += f"Product {row[0]}. " if row[0] else ''
            s += f"Marca {row[1]}." if row[1] else ''
            name_kustom.append(s)
        name = pd.Series(name_kustom)
        name = name.apply(lambda s: reduce_dots(s))

        # Build code field
        code = df[["codigo", "sku", "ean"]]
        code = code.apply(lambda row: row.to_list(), axis=1)
        code_kustom = []
        for row in code:
            s = ''
            s += f"Código {row[0]}. " if row[0] else ''
            s += f"Código SKU {row[1]}. " if row[1] else ''
            s += f"Código EAN {row[1]}. " if row[1] else ''
            code_kustom.append(s)
        code = pd.Series(code_kustom)
        code = code.apply(lambda s: reduce_dots(s))

        # Build features field
        no_features_columns = ["producto", "marca", "codigo", "sku", "ean"]
        features_columns = [col for col in Vichy.columns 
                            if col not in no_features_columns and 
                            col not in Vichy.columns_to_drop]
        features = df[features_columns]
        features = features.apply(lambda row: row.to_list(), axis=1)
        features_kustom = []
        for fts in features:
            s = ''
            for i, column_name in enumerate(features_columns):
                s += f"{column_name.capitalize()}: {fts[i]}. " if fts[i] else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))

        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        code.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
        dataframe = dataframe.map(str)
        dataframe = dataframe.apply(lambda s: s.replace('nan', ''))

        # Concatenate dataframes
        condition = (dataframe['Producto']=='') & (dataframe['Código']=='')
        dataframe = dataframe[~condition]

        return dataframe
    
    def to_txt(self, folderpath: str='../data/txt/bybrand/vichy/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = Vichy.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()

    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)


class LRP(object):
    BRAND_CAP = "La Roche-Posay"
    BRAND_LOWER = "la roche-posay"
    BRAND_UPPER = "LA ROCHE-POSAY"
    columns = ["ean", "producto", "descripcion", "tamaño", "unidades", "composicion", 
               "beneficio 1", "beneficio 2", "beneficio 3", "uso", "keywords"]
    
    def __init__(self, filepath:str) -> None:
        self.filepath = filepath
        self.df = pd.read_excel(filepath, engine=get_engine(filepath))
        self.df.columns = LRP.columns
        self.df = clear_dataframe(self.df)

        # Get some parameters
        self.n_samples = self.df.shape[0]
        self.n_features = self.df.shape[1]
        self.n_words = self.df.map(lambda x: len(x.split(' '))).sum().sum()
        self.n_chars = self.df.map(lambda x: len(x)).sum().sum()

    def unify(self) -> pd.DataFrame:
        """Unify main dataframe. Reduce columns to: product, code, features.
        Column names: 'Producto', 'Código' and 'Descripción'.

        Returns:
            pd.DataFrame: A modified copy of the main dataframe, with the only three common columns.
        """
        df = self.df.copy()

        # Build name field
        name = df['producto']
        name = name.apply(lambda s: f"Producto {s}. Marca {LRP.BRAND_CAP}." if s else f"Marca {LRP.BRAND_CAP}.")
        name = name.apply(lambda s: reduce_dots(s))

        # Build code field
        code = df['ean']
        code = code.apply(lambda s: f"Código EAN {s}." if s else '')
        code = code.apply(lambda s: reduce_dots(s))

        # Build features field
        keywords = df['keywords']
        keywords = keywords.apply(lambda kws: make_keywords([kws]))
        keywords = keywords.apply(lambda s: reduce_dots(s))
        keywords = keywords.apply(lambda s: f"Keywords: {s}" if s else '')

        presentation = df[["tamaño", "unidades"]]
        presentation = presentation.apply(lambda row: row.to_list(), axis=1)
        presentation_kustom = []
        for row in presentation:
            if row[0] and row[1]:
                s = f"Presentación {row[0]}{row[1]}."
            else:
                s = ''
            presentation_kustom.append(s)
        presentation = pd.Series(presentation_kustom)
        presentation = presentation.apply(lambda s: reduce_dots(s))

        no_features_columns = ["producto", "ean", "tamaño", "unidades", "keywords"]
        features_columns = [col for col in df.columns if col not in no_features_columns]
        features = df[features_columns]
        features = features.apply(lambda row: row.to_list(), axis=1)
        features_kustom = []
        for fts, ppt, kws in zip(features, presentation, keywords):
            s = ''
            for i, column_name in enumerate(features_columns):
                s += f"{column_name.capitalize()}: {fts[i]}. " if fts[i] else ''
            s += f"{ppt} " if ppt else ''
            s += f"{kws}" if kws else ''
            features_kustom.append(s)
        features = pd.Series(features_kustom)
        features = features.apply(lambda s: reduce_dots(s))
        
        # Reset index before building dataframe
        name.reset_index(drop=True, inplace=True)
        code.reset_index(drop=True, inplace=True)
        features.reset_index(drop=True, inplace=True)
        # Build unify dataframe
        dataframe = pd.DataFrame(data={'Producto':name, 'Código':code, 'Descripción':features})
        dataframe = dataframe.map(str)
        dataframe = dataframe.apply(lambda s: s.replace('nan', ''))

        return dataframe
    
    def to_txt(self, folderpath: str='../data/txt/bybrand/lrp/', separate: bool=False) -> None:
        dataframe = self.unify()
        lines = [f"{name} {code} {features}" for name, code, features in 
                 zip(dataframe['Producto'], dataframe['Código'], dataframe['Descripción'])]
        brand = LRP.BRAND_LOWER
        
        if separate:
            n_lines = len(lines)
            for i, line in enumerate(lines):
                i = '0'*(len(str(n_lines)) - len(str(i+1))) + str(i+1)
                filepath = folderpath + f'{brand}_{i}.txt'
                with open(filepath, 'w') as f:
                    f.write(line + '\n')

        filepath = folderpath + f'{brand}_all.txt'
        with open(filepath, 'w') as f:
            for line in lines[:-1]:
                f.write(line + '\n')
            f.write(lines[-1])
        f.close()

    def to_sql(self, dbname:str, tablename:str):
        df = self._prepare_to_llm()
        engine = create_engine(f'sqlite:{dbname}')
        df.to_sql(f'{tablename}', con=engine, if_exists='replace', index=False)