public class RedDrug extends Drug{
    private int addLife;

    // constructor
    public RedDrug(){}
    public RedDrug(String size){
        super(size);
        switch(size){
            case "Large":
                addLife = 120;
                break;
            case "Medium":
                addLife = 80;
                break;
            case "Small":
                addLife = 50;
                break;
            default:
                addLife = 0;
                break;
        }
    }
    public int getAddLife() { return addLife; }
}
