public class BlueDrug extends Drug{
    private int addMagic;

    // constructor
    public BlueDrug(){}
    public BlueDrug(String size){
        super(size);
        switch(size){
            case "Large":
                addMagic = 100;
                break;
            case "Medium":
                addMagic = 60;
                break;
            case "Small":
                addMagic = 30;
                break;
            default:
                addMagic = 0;
                break;
        }
    }

    public int getAddMagic() { return addMagic; }
}
