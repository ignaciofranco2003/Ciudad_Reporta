# Ciudad_Reporta

### Configuracion de la BDD
Cambiar los valores necesarios para poder conectarse con la BDD (al inicio del archivo "Ciudad_Reporta.py")
```
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='1234'
)
```


# scripts-python

### Para crear un entorno virtual
```python
py -m venv .venv
```
### Para activar el entorno virtual
```python
.venv\Scripts\activate
```
### Para instalar las librerias requeridas para este Script
```python
pip install -r req.txt
```
### Para ejecutar el script
```python
py Ciudad_Reporta.py
```
