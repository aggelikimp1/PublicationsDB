def show_message(message): #Εμφανίζει ένα μήνυμα επιτυχίας ή ενημέρωσης
    print(f"\n {message}")

def show_error(error_message): #Εμφανίζει ένα μήνυμα σφάλματος
    print(f"\n ΣΦΑΛΜΑ: {error_message}")

def show_menu(options, title="ΜΕΝΟΥ"): #εμφάνιση μενού
    print(f"\n=== {title} ===")
    for k, v in sorted(options.items(), key=lambda x: int(x[0])):
        print(f"{k}. {v}")
    print("0. Έξοδος")


def show_publications_list(publications, title="Δημοσιεύσεις"): #Εμφανίζει μια λίστα δημοσιεύσεων σε μορφή πίνακα
    if not publications:
        print(f"\n--- {title} ---")
        print("Δεν βρέθηκαν αποτελέσματα.")
        return

    print(f"\n--- {title} ---")
    print(f"{'DOI':<25} | {'Τίτλος':<50}")
    print("-" * 80)
    for pub in publications:
        #Κόβουμε τον τίτλο αν είναι πολύ μεγάλος
        display_title = (pub['Titlos'][:47] + '...') if len(pub['Titlos']) > 47 else pub['Titlos']
        print(f"{pub['DOI']:<25} | {display_title:<50}")

def show_publication_details(pub, authors=None, comments=None):  #Εμφανίζει όλες τις λεπτομέρειες μιας συγκεκριμένης δημοσίευσης
    print("\n" + "="*60)
    print(f"ΠΛΗΡΟΦΟΡΙΕΣ ΔΗΜΟΣΙΕΥΣΗΣ")
    print("="*60)
    print(f"Τίτλος:    {pub['Titlos']}")
    print(f"DOI:       {pub['DOI']}")
    print(f"Γλώσσα:    {pub['Glossa']}")
    print(f"Περίληψη:  {pub['Perilipsi'] if pub['Perilipsi'] else 'Δεν υπάρχει περίληψη.'}")
    print(f"URL:       {pub['URL']}")
    
    if authors:
        print(f"Συγγραφείς: {', '.join(authors)}")
    
    print("-" * 60)
    if comments:
        print("ΣΧΟΛΙΑ:")
        for c in comments:
            print(f"- [{c['Username']}]: {c['Keimeno_sxolioy']} ({c['Imeromhnia_sxolioy']})")
    else:
        print("Δεν υπάρχουν σχόλια για αυτή τη δημοσίευση.")
    print("="*60)

def print_folder_subtree(folders, root_id, pubs_by_folder=None, show_pubs=False):

    children_map = {}
    name_map = {}

    for f in folders:
        fid = f["id_fakelou"]
        parent_id = f["id_kyriou_fakelou"]
        name = f["Onoma"]

        name_map[fid] = name
        children_map.setdefault(parent_id, []).append((fid, name))

    for pid in children_map:
        children_map[pid].sort(key=lambda x: x[1].lower())

    def _print(node_id, prefix="", is_last=True):
        name = name_map.get(node_id, "(Άγνωστος)")
        connector = "└─ " if is_last else "├─ "
        print(f"{prefix}{connector}📂 {name} [{node_id}]")

        if show_pubs and pubs_by_folder is not None:
            pubs = pubs_by_folder.get(node_id, [])
            pub_prefix = prefix + ("   " if is_last else "│  ")
            for p in pubs:
                title = (p["Titlos"][:47] + "...") if len(p["Titlos"]) > 47 else p["Titlos"]
                print(f"{pub_prefix}   📄 {p['DOI']} | {title}")

        kids = children_map.get(node_id, [])
        new_prefix = prefix + ("   " if is_last else "│  ")
        for i, (child_id, _) in enumerate(kids):
            _print(child_id, new_prefix, is_last=(i == len(kids) - 1))

    root_name = name_map.get(root_id, "Γενικά")
    print(f"\n📁 {root_name} [{root_id}]")

    if show_pubs and pubs_by_folder is not None:
        for p in pubs_by_folder.get(root_id, []):
            title = (p["Titlos"][:47] + "...") if len(p["Titlos"]) > 47 else p["Titlos"]
            print(f"   📄 {p['DOI']} | {title}")

    kids = children_map.get(root_id, [])
    if not kids:
        print("   (Κανένας υποφάκελος)")
        return

    for i, (child_id, _) in enumerate(kids):
        _print(child_id, prefix="", is_last=(i == len(kids) - 1))


def show_users(users): #εμφανίζει τους χρήστες του συστήματος
    if not users:
        print("\nΔεν υπάρχουν χρήστες.")
        return

    print("\n--- ΧΡΗΣΤΕΣ ΣΥΣΤΗΜΑΤΟΣ ---")
    print(f"{'Username':<20} | Ρόλος")
    print("-" * 35)

    for u in users:
        role = "ADMIN" if u["Is_admin"] == 1 else "Χρήστης"
        print(f"{u['Username']:<20} | {role}")

def show_saved_publications_and_pick(saved_pubs): #εμφανίζει αποθηκευμένες δημοσιεύσεις
    if not saved_pubs:
        print("\nΔεν έχετε αποθηκευμένες δημοσιεύσεις.")
        return None

    print("\n--- ΟΙ ΑΠΟΘΗΚΕΥΜΕΝΕΣ ΔΗΜΟΣΙΕΥΣΕΙΣ ΣΑΣ ---")
    for i, pub in enumerate(saved_pubs, 1):
        print(f"{i}. {pub['Titlos']} (DOI: {pub['DOI']})")

    choice = input("\nΕπιλέξτε αριθμό (Enter για ακύρωση): ").strip()
    if choice == "":
        return None
    if not choice.isdigit():
        print("Μη έγκυρη επιλογή.")
        return None

    idx = int(choice) - 1
    if idx < 0 or idx >= len(saved_pubs):
        print("Μη έγκυρη επιλογή.")
        return None

    return saved_pubs[idx]["DOI"]

def show_most_used_keyword(username, result): #εμφανίζει την πιο συχνή λέξη-κλειδί στις δημοσιεύσεις του χρήστη
    print("\n--- ΠΙΟ ΣΥΧΝΗ ΛΕΞΗ-ΚΛΕΙΔΙ ΧΡΗΣΤΗ ---")

    if not result:
        print(f"Ο χρήστης '{username}' δεν έχει αποθηκευμένα άρθρα με λέξεις-κλειδιά.")
        return

    print(f"Χρήστης: {username}")
    print(f"Λέξη-κλειδί: {result['keyword']}")
    print(f"Πλήθος εμφανίσεων: {result['plithos']}")

def show_latest_comment(result): #εμφανίζει το πιο πρόσφατο σχόλιο
    print("\n--- ΠΙΟ ΠΡΟΣΦΑΤΟ ΣΧΟΛΙΟ ΣΤΟ ΣΥΣΤΗΜΑ ---")

    if not result:
        print("Δεν υπάρχουν σχόλια στο σύστημα.")
        return

    print(f"Χρήστης: {result['Username']}")
    print(f"DOI δημοσίευσης: {result['DOI']}")
    print(f"Ημερομηνία: {result['Imer_dimiourgias']}")
    print("Περιεχόμενο:")
    print(result['Periexomeno'])
