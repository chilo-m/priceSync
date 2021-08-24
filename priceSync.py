import csv
from typing import Counter
import xml.etree.ElementTree as ET
#import msvcrt


class product:
    # класс товара

    fieldnames = ["Код артикула","Цена","В наличии"]

    def __init__(self, ID="", Art=0, Price=0.0, Count=0):
        self.id = str(ID)
        try: 
            self.art = int(Art)
        except ValueError:
            # удаление лишних символов кроме цифр и преобразование в int
            self.art = int(''.join([i for i in Art if i.isdigit()]))
            # Второй вариант убрать пробел заменой
            #art = valueProp.find('Значение').text.replace(" ","")
        self.price = float(Price)
        try:
            self.count = int(Count)
        except ValueError:
            self.count = int(Count.split('.')[0])

    def set_id(self, ID):
        self.id = str(ID)

    def set_art(self, Art):
        try: 
            self.art = int(Art)
        except ValueError:
            # удаление лишних символов кроме цифр и преобразование в int
            self.art = int(''.join([i for i in Art if i.isdigit()]))

    def set_price(self, Price):
        self.price = float(Price)

    def set_count(self, Count):
        try:
            self.count = int(Count)
        except ValueError:
            self.count = int(Count.split('.')[0])

    def get_id(self):
        return self.id

    def get_art(self):
        return self.art
    
    def get_price(self):
        return self.price

    def get_count(self):
        return self.count

    def __str__(self):
        return "Код артикула: {} Цена: {} Остаток: {}".format(self.art, self.price, self.count)

    def __eq__(self, other):
        if (self.id == other.id 
        and self.art == other.art 
        and self.price == other.price 
        and self.count == other.count):
            return True
        else:
            return False

    def info(self):
        # вывод информации о товаре
        print("Код артикула: {} Цена: {} Остаток: {}".format(self.art, self.price, self.count))

class productList(product):
    # класс списка товаров
    
    arrCurProducts = []
    arrNewProducts = []   
    
    def append_cur(self,Product):
        self.arrCurProducts.append(Product)

    def append_new(self,Product):
        self.arrNewProducts.append(Product)

    def info_cur(self):
        print("Товары на сайте:")
        for p in self.arrCurProducts:   
            print(p)

    def info_new(self):
        print("Товары в 1С:")
        for p in self.arrNewProducts:   
            print(p)

    def __str__(self):
        s = "Товары на сайте:\n"
        for p in self.arrCurProducts:
            s+= "{}\n".format(p.__str__())
        s+= "Товары в 1С:\n"
        for p in self.arrNewProducts:
            s+= "{}\n".format(p.__str__())
        return s

    def csv_dict_reader_site(self, fcur):
        # Чтение csv файла текущих товаров
        print("--------Чтение CSV--------")
        reader = csv.DictReader(fcur, delimiter=';')
        for row in reader:
            if (row["Тип строки"] == "product_variant" or row["Тип строки"] == "variant"):
                self.append_cur(product(Art=row["Код артикула"], Price=row["Цена"]))
        print("---Чтение CSV завершено---")
    
    def xml_dict_reader_1c(self, fimport, foffers):
        print("--------Чтение XML--------")
        
        tree = ET.parse(fimport.name)
        root = tree.getroot()
        
        for prod in root.iter('Товар'):
            id = prod.find('Ид').text
            art = 0
            for valueProp in prod.iter('ЗначениеРеквизита'):
                if valueProp.find('Наименование').text == "Код":
                    # Получение значения Кода артикула                
                    art = valueProp.find('Значение').text
            self.append_new(product(ID = id, Art = art))
        
        print("{} done".format(fimport.name))

        tree = ET.parse(foffers.name)
        root = tree.getroot()     

        # счетчик для проверки чтобы обойтись без поиска объектов для ускорения
        i = 0

        for prod in root.iter('Предложение'):
            
            id = prod.find('Ид').text
            if id == self.arrNewProducts[i].get_id():
                try:
                    self.arrNewProducts[i].set_price(prod.find("Цены/Цена/ЦенаЗаЕдиницу").text)
                    self.arrNewProducts[i].set_count(prod.find('Количество').text)
                    i+=1
                except AttributeError:
                    print("Ошибка в чтении файла!\nТовар не распознан 'id': '{}'".format(id))
            else:
                """
                попытка найти соответствие товаров при несовпадающих номерах
                Будет долго из-за большой номенклатуры
                Проверяется по списку файла offers.xml в котором есть цены и остатки товаров,
                поэтому если элемента не будет в import.xml,
                то у товара останутся поля Стоимость и Количество по умолчанию 0.
                Если будет найден товар в offers.xml, а артикул его не будет найден, то выдет сообщение об ошибке
                """
                try:
                    check_j = False
                    for j in self.arrNewProducts:
                        if id == j.get_id():
                            i = self.arrNewProducts.index(j)                            
                            self.arrNewProducts[i].set_price(prod.find("Цены/Цена/ЦенаЗаЕдиницу").text)
                            self.arrNewProducts[i].set_count(prod.find('Количество').text)
                            i+=1
                            check_j = True
                            break
                    if check_j == False:
                        print("Артикул не найден! Данные товара:\n\"{}\"\nid = {} не найдены.\nПроверьте правильность выгрузки БД".format(prod.find('Наименование').text, id))
                except:
                    print("Ошибка в файлах выгрузки") 
                    #return

        print("{} done".format(foffers.name))

        print("Проверка целостности...")     
        #for prod in self.arrNewProducts:
            #if prod.get_price() == 0:
                #print("Ошибка при проверке целостности в файлах выгрузки!\n Товар с id: {} артикулом: {} без цены!".format(prod.get_id(), prod.get_art()))
        print("Проверка целостности завершена!") 
        print("---Чтение XML завершено---")
        return
    
    def sync_data(self):
        
        # Список словарей
        dataList = []

        print("---Поиск изменений---")

        # Поиск циклом соответствий артикулов
        for curProd in self.arrCurProducts:
            artTest = False
            for newProd in self.arrNewProducts:                
                if curProd.get_art() == newProd.get_art():
                    # Артикул найден
                    artTest = True
                    # Проверка наличия изменений
                    """
                    if (curProd.get_price() != newProd.get_price()
                    or  curProd.get_count() != newProd.get_count()):
                    """
                    # Проверка, выросли ла цена
                    if (curProd.get_price() < newProd.get_price()):

                        curProd.set_price(newProd.get_price())
                        curProd.set_count(newProd.get_count())
                        inner_dict = dict(zip(self.fieldnames, [curProd.get_art(),curProd.get_price(),curProd.get_count()]))
                        dataList.append(inner_dict)
                        #print("There ara changes: {}".format(inner_dict))

                        #print("cur Артикул: {} Цена: {}\nnew Артикул: {} Цена: {} Id: {}".format(curProd.get_art(),curProd.get_price(),newProd.get_art(),newProd.get_price(), newProd.get_id()))
                    #else:
                        #print("There ara NO changes 'Код артикула': {}".format(newProd.get_art()))
                    break
            try:
                if artTest == False:
                    print("Критическая ошибка! Артикул с сайта не найден в файлах 1с!\nАртикул: {} Id: {}".format(curProd.get_art()))
            except IndexError:
                print("Ошибка переполнения массива")
        print("---Поиск изменений завершен!---")
        return dataList

    def csv_dict_writer_site(self, fupdate):
        # Запись в файл CSV
        print("--------Запись CSV--------")

        writer = csv.DictWriter(fupdate, delimiter=',', fieldnames=self.fieldnames)
        writer.writeheader()
        for row in self.sync_data():
            writer.writerow(row)
                
        print("---Запись CSV завершена---")
        
if __name__ == "__main__":

    tp = product(1,2,3,4)

    pl = productList()    
    
    with open("products.csv") as fcur_obj:
        pl.csv_dict_reader_site(fcur_obj)

    with open("import.xml") as fimport_obj, open("offers.xml") as foffers_obj:
        pl.xml_dict_reader_1c(fimport_obj,foffers_obj)

    with open("update.csv", 'w') as fupdate_obj:
        pl.csv_dict_writer_site(fupdate_obj)

    #pl.info_cur()

    print ('конец')
