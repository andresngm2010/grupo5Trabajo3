import pyodbc
import tkinter as tk
from tkinter import ttk


class base_datos:

    def __init__(self, nombre):

        self.nombre_bdd = nombre

        connection = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\SQLEXPRESS;DATABASE='
                                    + self.nombre_bdd + ';Trusted_Connection=yes;')

        self.cursor = connection.cursor()

    def integridad_referencial(self):

        cursor = self.cursor
        tablas = []
        relaciones_existentes = []
        relaciones_faltantes = []
        todo = {}

        cursor.execute("SELECT table_name FROM INFORMATION_SCHEMA.TABLES")

        for c in cursor:
            t = c.__getattribute__('table_name')
            tablas.append(t)

        for tabla in tablas:
            cursor.execute("EXEC sp_fkeys '" + tabla + "'")
            for c in cursor:
                tabla_1 = c.__getattribute__('PKTABLE_NAME')
                tabla_2 = c.__getattribute__('FKTABLE_NAME')
                key = c.__getattribute__('FKCOLUMN_NAME')
                relaciones_existentes.append([tabla_1, tabla_2, key])

        cursor.execute("SELECT column_name , table_name FROM INFORMATION_SCHEMA.COLUMNS")

        for c in cursor:
            tabla = c.__getattribute__('table_name')
            columna = c.__getattribute__('column_name')

            if tabla == "sysdiagrams":
                continue

            if not tabla in todo:
                todo[tabla] = []

            todo[tabla].append(columna)

        for tabla1 in todo:
            for tabla2 in todo:
                if tabla1 == tabla2:
                    continue
                intersecciones = list(set(todo[tabla1]).intersection(todo[tabla2]))
                if not intersecciones == []:
                    for key in intersecciones:
                        if [tabla1, tabla2, key] in relaciones_existentes or \
                                [tabla2, tabla1, key] in relaciones_existentes or \
                                [tabla1, tabla2, key] in relaciones_faltantes or \
                                [tabla2, tabla1, key] in relaciones_faltantes:
                            continue
                        relaciones_faltantes.append([tabla1, tabla2, key])
        return [relaciones_existentes, relaciones_faltantes]

    def anomalias_triggers(self):
        triggers = {}

        consulta = """SELECT  
        sysobjects.name AS trigger_name  
        ,USER_NAME(sysobjects.uid) AS trigger_owner  
        ,s.name AS table_schema  
        ,OBJECT_NAME(parent_obj) AS table_name  
        ,OBJECTPROPERTY( id, 'ExecIsUpdateTrigger') AS isupdate  
        ,OBJECTPROPERTY( id, 'ExecIsDeleteTrigger') AS isdelete  
        ,OBJECTPROPERTY( id, 'ExecIsInsertTrigger') AS isinsert  
        ,OBJECTPROPERTY(id, 'ExecIsTriggerDisabled') AS [disabled]  
        FROM sysobjects  
        INNER JOIN sysusers  
        ON sysobjects.uid = sysusers.uid  
        INNER JOIN sys.tables t  
        ON sysobjects.parent_obj = t.object_id  
        INNER JOIN sys.schemas s  
        ON t.schema_id = s.schema_id  
        WHERE sysobjects.type = 'TR'"""

        self.cursor.execute(consulta)

        for c in self.cursor:
            key = c.__getattribute__('table_name')
            triggers[key] = []
            if c.__getattribute__('isupdate') == 1:
                triggers[key].append('UPDATE')
            if c.__getattribute__('isinsert') == 1:
                triggers[key].append('INSERT')
            if c.__getattribute__('isdelete') == 1:
                triggers[key].append('DELETE')
            if c.__getattribute__('disabled') == 1:
                triggers[key].append('Desactivado')
            else:
                triggers[key].append('Activo')

        return triggers

    def anomalias_datos(self):
        anomalias = []

        self.cursor.execute('dbcc checkconstraints with all_constraints')

        for c in self.cursor:
            tabla = c.__getattribute__("Table")
            error = c.__getattribute__("Where")
            anomalias.append([tabla, error])

        return anomalias


def analizar_temp():
    nombrebdd = caja_temp_nombre_bdd.get()
    bdd = base_datos(nombrebdd)

    relaciones_existentes_string = str(bdd.integridad_referencial()[0]).replace("],", "]\n")
    relaciones_faltantes_string = str(bdd.integridad_referencial()[1]).replace("],", "]\n")
    triggers_string = str(bdd.anomalias_triggers()).replace("],", "]\n")
    anomalias_string = str(bdd.anomalias_datos()).replace("],", "]\n")

    etiqueta_temp_relaciones_existentes_string = ttk.Label(text=relaciones_existentes_string)
    etiqueta_temp_relaciones_existentes_string.place(x=20, y=140)

    etiqueta_temp_relaciones_faltantes_string = ttk.Label(text=relaciones_faltantes_string)
    etiqueta_temp_relaciones_faltantes_string.place(x=220, y=140)

    etiqueta_temp_triggers_string = ttk.Label(text=triggers_string)
    etiqueta_temp_triggers_string.place(x=420, y=140)

    etiqueta_temp_anomalias_string = ttk.Label(text=anomalias_string)
    etiqueta_temp_anomalias_string.place(x=660, y=140)

    f = open('log_' + bdd.nombre_bdd + '_relaciones.txt', 'w')
    f.write('')
    f = open('log_' + bdd.nombre_bdd + '_relaciones.txt', 'a')
    f.write("Relaciones Existentes\n" + relaciones_existentes_string +
            '\n\n' +
            "Relaciones Posibles/Faltantes\n" + relaciones_faltantes_string)
    f.close()
    f = open('log_' + bdd.nombre_bdd + '_triggers.txt', 'w')
    f.write('')
    f = open('log_' + bdd.nombre_bdd + '_triggers.txt', 'a')
    f.write("Triggers\n" + triggers_string)
    f.close()
    f = open('log_' + bdd.nombre_bdd + '_anomalias.txt', 'w')
    f.write('')
    f = open('log_' + bdd.nombre_bdd + '_anomalias.txt', 'a')
    f.write("Anomalias de Datos\n" + anomalias_string)
    f.close()


ventana = tk.Tk()
ventana.title("Auditoria de anomalias - Grupo 5")
ventana.config(width=1000, height=600)
etiqueta_temp_base_de_datos = ttk.Label(text="Ingrese la base de datos:")
etiqueta_temp_base_de_datos.place(x=20, y=20)
caja_temp_nombre_bdd = ttk.Entry()
caja_temp_nombre_bdd.place(x=180, y=20, width=60)
boton_analizar = ttk.Button(text="Analizar", command=analizar_temp)
boton_analizar.place(x=20, y=60)


etiqueta_temp_relaciones_existentes = ttk.Label(text="Relaciones Existentes:")
etiqueta_temp_relaciones_existentes.place(x=20, y=120)

etiqueta_temp_relaciones_faltantes = ttk.Label(text="Relaciones Faltantes:")
etiqueta_temp_relaciones_faltantes.place(x=220, y=120)

etiqueta_temp_triggers = ttk.Label(text="Triggers:")
etiqueta_temp_triggers.place(x=420, y=120)

etiqueta_temp_anomalias = ttk.Label(text="Anomalias de datos:")
etiqueta_temp_anomalias.place(x=660, y=120)

ventana.mainloop()