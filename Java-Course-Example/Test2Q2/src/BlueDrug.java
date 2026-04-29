
public class BlueDrug extends Drug {
	
	private int addMagic;
	//Àq»{ºc³y¨ç¼Æ
     public BlueDrug() {
		
	}
	public BlueDrug(String size) {
		super(size);
		switch(size) {
		case "large":
			addMagic = 100;
			break;
		case "medium":
			addMagic = 60;
			break;
			
		case "small":
			addMagic = 30;
			break;
		default:
			System.out.println("No such BlueDrug size->" +size);
			addMagic = 0;
		}
	}
	//Set
	public void setAddMagic(int addMagic) {
		this.addMagic = addMagic;
	}
	//Get
	public int getAddMagic() {
		return  addMagic;
	}
	
}
