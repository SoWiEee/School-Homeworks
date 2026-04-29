public class RedDrug extends Drug {
    private int addLife;

    // constructor
    public RedDrug() {}
    public RedDrug(String size) {
        super(size);
        switch (size) {
            case "large":
                addLife = 120;
                break;
            case "middle":
                addLife = 80;
                break;
            case "small":
                addLife = 50;
                break;
            default:
                addLife = 0;
                break;
        }
    }

    public int getAddLife() { return addLife; }
}
