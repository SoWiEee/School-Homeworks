public class Role {
    private String Name;
    private int Life;
    private int Magic;
    // constructor
    public Role() {
        Name = "None";
        Life = 100;
        Magic = 100;
    }
    public Role(String Name, int Life, int Magic) {
        this.Name = Name;
        this.Life = Life;
        this.Magic = Magic;
    }

    // getter & setter
    public String getName() { return Name; }
    public int getLife() { return Life; }
    public int getMagic() { return Magic; }
    public void setLife(int Life) { this.Life = Life; }
    public void setMagic(int Magic) { this.Magic = Magic;}
}