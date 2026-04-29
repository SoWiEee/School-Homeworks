public abstract class Role implements Personate {
    private String name;
    private int life;
    private int magic;

    // constructor
    public Role() {
        this.name="";
        this.life=0;
        this.magic=0;
    }
    public Role(String name, int life, int magic) {
        this.name = name;
        this.life = life;
        this.magic = magic;
    }

    // getter & setter
    public int getLife() { return life; }
    public int getMagic() { return magic; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public void setLife(int life) { this.life = life; }
    public void setMagic(int magic) { this.magic = magic; }

    // drink drug
    public abstract void Drink(Drug D);
}
