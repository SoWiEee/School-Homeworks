abstract public class Drug {
    private String size;

    public Drug() { size = "small"; }
    public Drug(String size) { this.size = size; }

    public String getSize() { return size; }
    public void setSize(String size) { this.size = size; }
}