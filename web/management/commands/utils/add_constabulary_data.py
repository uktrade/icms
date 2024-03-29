from web.models import Constabulary

constabulary_data = [
    ("Avon & Somerset", "SW", True, "02044887024"),
    ("Bedfordshire", "ER", True, "02037914104"),
    ("Cambridgeshire", "ER", True, "01091948164"),
    ("Central Scotland", "SC", False, "01040683048"),
    ("Cumbria", "NW", True, "01026278481"),
    ("Cheshire", "NW", True, "01026660505"),
    ("City of London", "LO", True, "02068796524"),
    ("Cleveland", "NE", True, "02073700521"),
    ("Devon & Cornwall", "SW", True, "01013570143"),
    ("Dorset", "SW", True, "01082267781"),
    ("Dumfries & Galloway", "SC", False, "02044499614"),
    ("Durham", "NE", True, "01052624293"),
    ("Essex", "ER", True, "01016897069"),
    ("Gloucestershire", "SW", True, "01055565849"),
    ("Derbyshire", "EM", True, "01067550960"),
    ("Dyfed-Powys", "SW", True, "01033363650"),
    ("Fife", "SC", False, "02076361985"),
    ("Grampian", "SC", False, "01078539865"),
    ("Greater Manchester", "NW", True, "02031834454"),
    ("Gwent", "SW", True, "02046283918"),
    ("Hampshire", "SE", True, "01015867769"),
    ("Hertfordshire", "ER", True, "01081440278"),
    ("Humberside", "NE", True, "02052769213"),
    ("Isle of Man 1", "IM", False, "01056895558"),
    ("Kent", "SE", True, "01028108560"),
    ("Lancashire", "NW", True, "02027042163"),
    ("Leicestershire", "EM", True, "02036618246"),
    ("Lincolnshire", "EM", True, "01003688734"),
    ("Lothian & Borders", "SC", False, "02015183124"),
    ("Merseyside", "NW", True, "02015665475"),
    ("Metropolitan", "LO", True, "01011674640"),
    ("Norfolk", "ER", True, "02076207448"),
    ("North Wales", "NW", True, "01084721044"),
    ("North Yorkshire", "NE", True, "01020677504"),
    ("Northamptonshire", "EM", True, "01047947755"),
    ("Northern", "SC", False, "02074951190"),
    ("Northumbria", "NE", True, "01097745302"),
    ("Nottingham", "EM", True, "01080495915"),
    ("Police Service of Northern Ireland", "RU", True, "01096171312"),
    ("South Wales", "SW", True, "01054447826"),
    ("South Yorkshire", "NE", True, "01061306869"),
    ("Staffordshire", "WM", True, "02050621111"),
    ("Strathclyde", "SC", False, "01031718126"),
    ("Suffolk", "ER", True, "02002415073"),
    ("Surrey", "SE", True, "01029806953"),
    ("Sussex", "SE", True, "02081943313"),
    ("Tayside", "SC", False, "01088575749"),
    ("Thames Valley", "SE", True, "01081188175"),
    ("Warwickshire", "WM", True, "02064147048"),
    ("West Mercia", "WM", True, "01075602813"),
    ("West Midlands", "WM", True, "01090545513"),
    ("West Yorkshire", "NE", True, "01034697220"),
    ("Wiltshire", "SW", True, "01065850950"),
    ("Scotland (Aberdeen)", "SC", True, "02004495434"),
    ("Scotland (Dumfries)", "SC", True, "01061684693"),
    ("Scotland (Dundee)", "SC", True, "02093433996"),
    ("Scotland (Edinburgh)", "SC", True, "02054017059"),
    ("Scotland (Glasgow)", "SC", True, "02093621098"),
    ("Scotland (Glenrothes)", "SC", True, "02001038275"),
    ("Scotland (Inverness)", "SC", True, "01015606111"),
    ("Scotland (Stirling)", "SC", True, "01092620414"),
    ("Scotland (Scottish Executive)", "SC", True, "01003589948"),
    ("Metropolitan Police (ILB use only) closed 30/06/16", "LO", False, "02022146704"),
    ("Home Office 1", "LO", True, "01062057866"),
    ("Essex (ILB use only 1)", "SE", True, "01018557562"),
    ("Essex (ILB use only 2)", "SE", True, "02046128618"),
    ("Greater Manchester Police (ILB ONLY)", "NW", True, "01018277611"),
    ("West Mercia (ILB Use Only)", "WM", True, "01080718913"),
    ("Metropolitan Police (ILB use only)", "LO", True, "02038595709"),
    ("MoD - P Sonnex", "LO", False, "01001521896"),
    ("Proof House - Birmingham (ILB USE ONLY)", "WM", True, "02017750877"),
    ("MoD - D Walker", "LO", True, "01055821068"),
    ("Home Office 2", "LO", True, "01013025295"),
    ("Home Office 3", "LO", True, "02060586973"),
    ("Home Office 4 - section 58(2)", "LO", False, "01039813315"),
    ("Home Office 5 - section 58(2)", "LO", True, "01000216404"),
    ("Isle of Man 2", "IM", False, "01052116405"),
    ("Isle of Man 3", "IM", False, "01024863274"),
    ("Isle of Man", "IM", True, "01019568203"),
]


def add_constabulary_data():
    new_records = []

    for i, (name, region, is_active, telephone_number) in enumerate(constabulary_data):
        new_records.append(
            Constabulary(
                name=name,
                region=region,
                email=f"constabulary-{i}-{region}@example.com",
                is_active=is_active,
                telephone_number=telephone_number,
            )
        )

    Constabulary.objects.bulk_create(new_records)
