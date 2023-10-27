from RTW2FM import RTW

def main():
    rtw = RTW("RTW.txt")
    rtw.convertToXML("model.xml", showTag=True)
    
if __name__=="__main__":
    main()
