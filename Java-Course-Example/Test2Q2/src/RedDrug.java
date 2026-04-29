
public class RedDrug extends Drug {
	
	private int addLife;
	
	//Àq»{ºc³y¨ç¼Æ
	public RedDrug() {
		
	}
public RedDrug(String size) {
	super(size);
	switch(size) {
	case "large":
		addLife = 120;
		break;
	case "medium":
		addLife = 80;
	case "small":
		addLife = 50;
		break;
	default:
		System.out.println("No such RedDrug size -->" + size);
		addLife = 0;
	}
}

public void setAddLife(int addLife) {
	this.addLife=addLife;
}
public int getAddLife() {
	return addLife;
}

}
