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

        cursor.execute("SELECT table_name, table_schema FROM INFORMATION_SCHEMA.TABLES")

        for c in cursor:
            tn = c.__getattribute__('table_name')
            ts = c.__getattribute__('table_schema')
            tablas.append([tn, ts])

        for tabla in tablas:
            tn = tabla[0]
            ts = tabla[1]
            cursor.execute("EXEC sp_fkeys @pktable_name = '"+tn+"' "
                           ",@pktable_owner = '"+ts+"';")
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
        cursor = self.cursor
        triggers = {}

        consulta = "SELECT sysobjects.name AS trigger_name" \
                   " ,USER_NAME(sysobjects.uid) AS trigger_owner  " \
                   ",s.name AS table_schema  " \
                   ",OBJECT_NAME(parent_obj) AS table_name  " \
                   ",OBJECTPROPERTY( id, 'ExecIsUpdateTrigger') AS isupdate  " \
                   ",OBJECTPROPERTY( id, 'ExecIsDeleteTrigger') AS isdelete  " \
                   ",OBJECTPROPERTY( id, 'ExecIsInsertTrigger') AS isinsert  " \
                   ",OBJECTPROPERTY(id, 'ExecIsTriggerDisabled') AS [disabled]  " \
                   "FROM sysobjects  " \
                   "INNER JOIN sysusers  " \
                   "ON sysobjects.uid = sysusers.uid  " \
                   "INNER JOIN sys.tables t  " \
                   "ON sysobjects.parent_obj = t.object_id  " \
                   "INNER JOIN sys.schemas s  " \
                   "ON t.schema_id = s.schema_id  " \
                   "WHERE sysobjects.type = 'TR'"

        cursor.execute(consulta)

        for c in cursor:
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
        cursor = self.cursor
        anomalias = []

        try:
            cursor.execute('dbcc checkconstraints with all_constraints')
            for c in cursor:
                tabla = c.__getattribute__("Table")
                error = c.__getattribute__("Where")
                anomalias.append([tabla, error])
        except:
            anomalias.append("No se han encontrado anomalias")

        return anomalias


def analizar_temp():
    nombrebdd = caja_temp_nombre_bdd.get()
    bdd = base_datos(nombrebdd)

    relaciones_existentes_string = str(bdd.integridad_referencial()[0]).replace("],", "]\n")
    relaciones_faltantes_string = str(bdd.integridad_referencial()[1]).replace("],", "]\n")
    triggers_string = str(bdd.anomalias_triggers()).replace("],", "]\n")
    anomalias_string = str(bdd.anomalias_datos()).replace("],", "]\n")

    etiqueta_temp_relaciones_existentes_string = ttk.Label(text=relaciones_existentes_string, background="bisque")
    etiqueta_temp_relaciones_existentes_string.grid(column=0, row=3, padx=4, pady=4, sticky="nw")

    etiqueta_temp_relaciones_faltantes_string = ttk.Label(text=relaciones_faltantes_string, background="bisque")
    etiqueta_temp_relaciones_faltantes_string.grid(column=1, row=3, padx=4, pady=4, sticky="nw")

    etiqueta_temp_triggers_string = ttk.Label(text=triggers_string, background="bisque")
    etiqueta_temp_triggers_string.grid(column=2, row=3, padx=4, pady=4, sticky="nw")

    etiqueta_temp_anomalias_string = ttk.Label(text=anomalias_string, background="bisque")
    etiqueta_temp_anomalias_string.grid(column=3, row=3, padx=4, pady=4, sticky="nw")

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
ventana.config(background="blanched almond")

etiqueta_temp_base_de_datos = ttk.Label(text="Ingrese la base de datos:", background="bisque")
etiqueta_temp_base_de_datos.grid(column=0, row=0, padx=4, pady=4, sticky="nw")

caja_temp_nombre_bdd = ttk.Entry()
caja_temp_nombre_bdd.grid(column=1, row=0, padx=4, pady=4, sticky="nw")

boton_analizar = tk.Button(text="Analizar", command=analizar_temp, bg="bisque")
boton_analizar.grid(column=1, row=1, padx=4, pady=4, sticky="nw")

etiqueta_temp_relaciones_existentes = ttk.Label(text="Relaciones Existentes:", background="bisque")
etiqueta_temp_relaciones_existentes.grid(column=0, row=2, padx=4, pady=4, sticky="nw")

etiqueta_temp_relaciones_faltantes = ttk.Label(text="Relaciones Faltantes:", background="bisque")
etiqueta_temp_relaciones_faltantes.grid(column=1, row=2, padx=4, pady=4, sticky="nw")

etiqueta_temp_triggers = ttk.Label(text="Triggers:", background="bisque")
etiqueta_temp_triggers.grid(column=2, row=2, padx=4, pady=4, sticky="nw")

etiqueta_temp_anomalias = ttk.Label(text="Anomalias de datos:", background="bisque")
etiqueta_temp_anomalias.grid(column=3, row=2, padx=4, pady=4, sticky="nw")

ventana.mainloop()