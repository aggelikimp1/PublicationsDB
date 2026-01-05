import getpass
from model import (get_all_publications, get_saved_publications, get_folder_publications_details, insert_publication, delete_publication,
                    get_publication_by_doi, get_pub_type, get_detailed_pub_info, get_all_authors, insert_author,
                     get_authors_from_publication, link_author_to_publication, get_all_institutions,
                     get_keywords_for_publication, get_keyword_id, insert_new_keyword, insert_keyword, get_most_used_keyword_for_user,
                     search_publications, search_authors, get_pubs_by_author, get_pubs_by_keyword, update_pub_title, update_username,
                     get_folder_parent_id, is_in_general_subtree, get_comments_by_pub_and_user, insert_comment_to_pub, delete_comment, get_latest_comment_with_doi,
                     get_or_create_folder, add_pub_to_folder, remove_pub_from_folder, get_user_folders, get_subfolders, 
                     delete_folder, hash_password, new_user, delete_user_account, get_user_by_username, verify_user, get_all_usernames, is_admin, get_connection)

from view import (show_message, show_error, show_menu, show_publications_list, show_publication_details, print_folder_subtree, show_users, show_saved_publications_and_pick,
                  show_most_used_keyword, show_latest_comment)

class BackToMenu(Exception):
    """Χρησιμοποιείται για να επιστρέφουμε άμεσα στο προηγούμενο μενού."""
    pass

starting_options = {
    "1": "Σύνδεση",
    "2": "Εγγραφή"
}

user_options = {
    "1": "Εμφάνιση αποθηκευμένων δημοσιεύσεων και φακέλων",
    "2": "Προβολή λεπτομερειών δημοσίευσης",
    "3": "Προσθήκη δημοσίευσης",
    "4": "Διαγραφή δημοσίευσης",
    "5": "Δημιουργία φακέλου",
    "6": "Διαγραφή φακέλου",
    "7": "Δημιουργία σχολίου",
    "8": "Διαγραφή σχολίου",
    "9": "Προβολή σχολίων μιας δημοσίευσης",
    "10": "Αναζήτηση δημοσίευσης με βάση τίτλο ή DOI",
    "11": "Αναζήτηση δημοσίευσης με βάση συγγραφέα",
    "12": "Αναζήτηση δημοσίευσης με βάση λέξη-κλειδί"

}

admin_options = {
    "1": "Προσθήκη δημοσίευσης",
    "2": "Τροποποίηση δημοσίευσης",
    "3": "Διαγραφή δημοσίευσης",
    "4": "Προβολή δημοσίευσεων", 
    "5": "Προβολή συγγραφέων και ιδρυμάτων",
    "6": "Προβολή χρηστών",
    "7": "Διαγραφή χρήστη",
    "8": "Προβολή πιο πρόσφατου σχόλιου χρήστη",
    "9": "Προτίμηση χρήστη (λέξη-κλειδί)"

}

def get_user_input(prompt):
    value = input(f"{prompt} (ή 'q' για ακύρωση): ").strip()
    if value.lower() == "q":
        raise BackToMenu()
    return value


def sign_in(): #σύνδεση χρήστη
    username = input("Εισάγετε το username σας: ").strip()
    password = getpass.getpass("Εισάγετε τον κωδικό πρόσβασης σας: ")
    try:
        user = verify_user(username, password)
        if not user:
            show_error("Λάθος username ή κωδικός.")
            return None
        print("\nΕπιτυχής σύνδεση.\n")
        return user
    except Exception as e:
        show_error(f"Σφάλμα σύνδεσης: {e}")
        return None


def sign_up(): #εγγραφή χρήστη
    email = input("Εισάγετε το email σας: ").strip()
    fullname = input("Εισάγετε το ονοματεπώνυμο σας: ").strip()
    username = input("Εισάγετε username: ").strip()
    password = getpass.getpass("Εισάγετε κωδικό πρόσβασης: ")
    user = {'username': username, 'password': password, 'email': email, 'fullname': fullname}
    try:
        new_user(user['username'], user['email'], user['fullname'], user['password'])
        print("\nΕπιτυχής εγγραφή.\n")
        return True
    except ValueError as e:
        show_error(str(e))
        return False

def show_general_subtree(username):
    try:
        general_id = get_or_create_folder("Γενικά", username)

        folders = get_user_folders(username) 

        pubs_by_folder = {}
        for f in folders:
            fid = f["id_fakelou"]
            pubs_by_folder[fid] = get_folder_publications_details(fid, username) 

        print_folder_subtree(folders, general_id, pubs_by_folder=pubs_by_folder, show_pubs=True)

    except BackToMenu:
        raise
    except Exception as e:
        show_error(f"Σφάλμα κατά την εμφάνιση subtree: {e}")



def show_folder_contents_detailed(folder_id, username): #περιεχόμενα φακέλου
    subfolders = get_subfolders(folder_id, username) 
    pubs = get_folder_publications_details(folder_id, username) 

    print("\n📁 Υποφάκελοι:")
    if not subfolders:
        print("  (Κανένας υποφάκελος)")
    else:
        for fid, name in subfolders:
            print(f"  [{fid}] {name}")

    show_publications_list(pubs, title="📄 Δημοσιεύσεις στον φάκελο")

def show_folder_under_general(username): #εμφανίζει υποφακέλους
    try:
        general_id = get_or_create_folder("Γενικά", username)

        print_folder_subtree(username, general_id, show_pubs=False)

        raw = get_user_input("\nΔώστε το ID του φακέλου που θέλετε να εμφανίσετε: ")
        if not raw.isdigit():
            show_error("Μη έγκυρο ID.")
            return

        folder_id = int(raw)

        if not is_in_general_subtree(folder_id, general_id, username):
            show_error("Ο φάκελος δεν βρίσκεται μέσα στον 'Γενικά'.")
            return

        show_folder_contents_detailed(folder_id, username)

    except BackToMenu:
        raise

    except Exception as e:
        show_error(f"Σφάλμα στην επιλογή 'Εμφάνιση φακέλου': {e}")

def view_saved_pub_details(username):
    try:
        saved_pubs = get_saved_publications(username) 

        selected_doi = show_saved_publications_and_pick(saved_pubs)  
        if selected_doi is None:
            return

        pub_data = get_publication_by_doi(selected_doi)  
        if not pub_data:
            show_error("Δεν βρέθηκε η δημοσίευση.")
            return

        p_type = get_pub_type(selected_doi)
        extra_info = get_detailed_pub_info(selected_doi, p_type)

        show_publication_details(pub_data)

        if extra_info:
            print(f"Επιπλέον στοιχεία ({p_type}):")
            for k, v in extra_info.items():
                print(f"  {k}: {v}")

    except BackToMenu:
        raise

    except Exception as e:
        show_error(f"Σφάλμα κατά την προβολή λεπτομερειών: {e}")



def show_comments_for_pub(username): #προβολή σχολίων του χρήστη για μια δημοσίευση
    doi = get_user_input("Εισάγετε το DOI της δημοσίευσης για να δείτε τα σχόλιά σας: ")
    if not doi:
        show_error("Το DOI δεν μπορεί να είναι κενό.")
        return

    try:
        comments = get_comments_by_pub_and_user(doi, username)

        if not comments:
            print(f"\nΔεν έχετε γράψει σχόλια στη δημοσίευση με DOI: {doi}")
            return

        print(f"\n--- ΤΑ ΣΧΟΛΙΑ ΣΑΣ ΓΙΑ ΤΗ ΔΗΜΟΣΙΕΥΣΗ {doi} ---")
        for c in comments:
            print(f"ID: {c['id_sxoliou']} | Ημερομηνία: {c['Imer_dimiourgias']}")
            print(f"Σχόλιο: {c['Periexomeno']}")
            print("-" * 40)

    except BackToMenu:
        raise

    except Exception as e:
        show_error(f"Σφάλμα κατά την ανάκτηση σχολίων: {e}")

def add_publication(username): #προσθήκη δημοσίευσης
    doi = get_user_input("Εισάγετε το DOI της δημοσίευσης: ")
    if not doi:
        show_error("Το DOI δεν μπορεί να είναι κενό.")
        return

    confirm = get_user_input("Θέλετε να ορίσετε συγκεκριμένο φάκελο; (ν/ο): ")

    try:
        general_id = get_or_create_folder("Γενικά", username) 

        if confirm == "ν":
            folder_name = get_user_input("Εισάγετε όνομα φακέλου: ")
            if not folder_name:
                show_error("Το όνομα φακέλου δεν μπορεί να είναι κενό.")
                return

            folder_id = get_or_create_folder(folder_name, username, parent_id=general_id)
        else:
            #Default:"Γενικά"
            folder_id = general_id

        add_pub_to_folder(doi, folder_id, username)
        show_message("Επιτυχής εισαγωγή δημοσίευσης σε φάκελο.")

    except BackToMenu:
        raise

    except ValueError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"Σφάλμα κατά την προσθήκη δημοσίευσης: {e}")


def delete_publication_from_folder(username): #διαγραφή δημοσίευσης από φάκελο
    try:
        doi = get_user_input("Εισάγετε το DOI της δημοσίευσης που θέλετε να αφαιρέσετε: ")
        if not doi:
            show_error("Το DOI δεν μπορεί να είναι κενό.")
            return

        general_id = get_or_create_folder("Γενικά", username)
        user_folders = get_user_folders(username)

        print_folder_subtree(username, general_id, show_pubs=False)

        raw = get_user_input("\nΔώστε το ID του φακέλου από τον οποίο θα αφαιρεθεί η δημοσίευση: ")
        if not raw.isdigit():
            show_error("Μη έγκυρο ID.")
            return
        folder_id = int(raw)

        if not is_in_general_subtree(folder_id, general_id, username):
            show_error("Ο φάκελος δεν βρίσκεται μέσα στον 'Γενικά'.")
            return

        confirm = get_user_input(f"Θέλετε σίγουρα να αφαιρέσετε το DOI {doi} από τον φάκελο ID {folder_id}; (ν/ο): ")
        if confirm != "ν":
            show_message("Ακύρωση αφαίρεσης δημοσίευσης.")
            return

        remove_pub_from_folder(doi, folder_id, username)
        show_message("Η δημοσίευση αφαιρέθηκε επιτυχώς από τον φάκελο.")

    except BackToMenu:
        raise

    except LookupError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"Σφάλμα κατά την αφαίρεση δημοσίευσης: {e}")


def new_folder(username): #δημιουργία φακέλου
    folder_name = get_user_input("Εισάγετε το όνομα του φακέλου για δημιουργία: ")
    if not folder_name:
        show_error("Το όνομα φακέλου δεν μπορεί να είναι κενό.")
        return

    confirm = get_user_input("Θέλετε να ορίσετε κύριο φάκελο; (ν/ο): ")

    try:
        if confirm == "ν":
            parent_name = get_user_input("Εισάγετε το όνομα του κύριου φακέλου: ")
            if not parent_name:
                show_error("Το όνομα του κύριου φακέλου δεν μπορεί να είναι κενό.")
                return

            parent_id = get_or_create_folder(parent_name, username)

        else:
            parent_id = get_or_create_folder("Γενικά", username)

        folder_id = get_or_create_folder(folder_name, username, parent_id)
        print("Επιτυχής δημιουργία φακέλου.")

    except BackToMenu:
        raise

    except ValueError as e:
        show_error(str(e))

def delete_user_folder(username): #διαγραφή φακέλου από τον χρήστη
    try:
        general_id = get_or_create_folder("Γενικά", username)
        user_folders = get_user_folders(username)

        print_folder_subtree(username, general_id, show_pubs=False)

        raw = get_user_input("\nΔώστε το ID του φακέλου που θέλετε να διαγράψετε: ")
        if not raw.isdigit():
            show_error("Μη έγκυρο ID.")
            return
        folder_id = int(raw)

        if folder_id == general_id:
            show_error("Δεν μπορείτε να διαγράψετε τον φάκελο 'Γενικά'.")
            return

        if not is_in_general_subtree(folder_id, general_id, username):
            show_error("Ο φάκελος δεν βρίσκεται μέσα στον 'Γενικά'.")
            return

        confirm = input(f"Θέλετε σίγουρα να διαγράψετε τον φάκελο με ID {folder_id}; (ν/ο): ").strip().lower()
        if confirm != "ν":
            show_message("Ακύρωση διαγραφής φακέλου.")
            return

        delete_folder(folder_id, username)
        show_message("Επιτυχής διαγραφή φακέλου.")

    except BackToMenu:
        raise
    except LookupError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"Σφάλμα κατά τη διαγραφή φακέλου: {e}")


def create_comment(username): #δημιουργία σχολίου σε δημοσίευση
    doi = get_user_input("Εισάγετε το doi της δημοσίευσης: ")
    comment = get_user_input("Γράψτε το σχόλιο: ")

    try:
        insert_comment_to_pub(doi, username, comment)
        print("Επιτυχής εισαγωγή σχολίου.")

    except BackToMenu:
        raise
    except ValueError as e:
        print(e)
    except Exception as e:
        print("Παρουσιάστηκε απρόσμενο σφάλμα:", e)

def delete_user_comment(username): #διαγραφή σχολίου από τον χρήστη
    doi = get_user_input("Εισάγετε το DOI της δημοσίευσης στην οποία είναι το σχόλιο: ")

    try:
        comments = get_comments_by_pub_and_user(doi, username)

        if not comments:
            print("Δεν έχετε γράψει σχόλια σε αυτή τη δημοσίευση.")
            return

        print("\nΤα σχόλιά σας:")
        for c in comments:
            print(f"[{c['id_sxoliou']}] {c['Periexomeno']}")

        try:
            comment_id = int(get_user_input("\nΔώστε το ID του σχολίου που θέλετε να διαγράψετε: "))
        except BackToMenu:
            raise
        except ValueError:
            show_error("Μη έγκυρο ID σχολίου.")
            return

        confirm = get_user_input(f"Θέλετε σίγουρα να διαγράψετε το σχόλιο με ID {comment_id}; (ν/ο): ")

        if confirm != "ν":
            print("Ακύρωση διαγραφής σχολίου.")
            return

        delete_comment(comment_id, username)
        print("Επιτυχής διαγραφή σχολίου.")

    except BackToMenu:
        raise
    except LookupError as e:
        show_error(str(e))

    except Exception as e:
        show_error(f"Σφάλμα κατά τη διαγραφή σχολίου: {e}")

def search_pub(): #αναζήτηση δημοσίευσης με βάση τίτλο ή DOI
    search = get_user_input("Εισάγετε το DOI ή τον τίτλο της δημοσίευσης: ")

    if not search:
        show_error("Η αναζήτηση δεν μπορεί να είναι κενή.")
        return

    try:
        results = search_publications(search)

        if not results:
            print("Δεν βρέθηκαν δημοσιεύσεις.")
            return

        print("\nΑποτελέσματα αναζήτησης:")
        for pub in results:
            print(f"- {pub['DOI']} | {pub['Titlos']}")

    except BackToMenu:
        raise
    except Exception as e:
        show_error(f"Σφάλμα κατά την αναζήτηση: {e}")

def search_pub_by_author(): #αναζήτηση δημοσίευσης με βάση τον συγγραφέα
    name = get_user_input("Εισάγετε ονοματεπώνυμο συγγραφέα: ")
    if not name:
        show_error("Η αναζήτηση δεν μπορεί να είναι κενή.")
        return

    try:
        authors = search_authors(name)
        if not authors:
            print("Δεν βρέθηκαν συγγραφείς.")
            return

        print("\nΑποτελέσματα συγγραφέων:")
        for a in authors:
            print(f"- {a['id_syggrafea']} | {a['Onomateponymo']}")

        chosen = get_user_input("\nΕισάγετε το id του συγγραφέα από τη λίστα: ")
        if not chosen:
            show_error("Πρέπει να επιλέξετε id συγγραφέα.")
            return
        if not chosen.isdigit():
            show_error("Το id πρέπει να είναι αριθμός.")
            return

        author_id = int(chosen)
        pubs = get_pubs_by_author(author_id)

        if not pubs:
            print("Δεν βρέθηκαν δημοσιεύσεις για τον επιλεγμένο συγγραφέα.")
            return

        print("\nΔημοσιεύσεις συγγραφέα:")
        for pub in pubs:
            print(f"- {pub['DOI']} | {pub['Titlos']}")

    except BackToMenu:
        raise
    except Exception as e:
        show_error(f"Σφάλμα κατά την αναζήτηση: {e}")

def search_pub_by_keyword(): #αναζήτηση δημοσίευσης με βάση λέξη-κλειδί
    keyword = get_user_input("Εισάγετε λέξη-κλειδί: ")
    if not keyword:
        show_error("Η αναζήτηση δεν μπορεί να είναι κενή.")
        return

    try:
        results = get_pubs_by_keyword(keyword)
        if not results:
            print("Δεν βρέθηκαν δημοσιεύσεις για τη συγκεκριμένη λέξη-κλειδί.")
            return

        print("\nΑποτελέσματα αναζήτησης:")
        for pub in results:
            print(f"- {pub['DOI']} | {pub['Titlos']}")

    except BackToMenu:
        raise
    except Exception as e:
        show_error(f"Σφάλμα κατά την αναζήτηση: {e}")

def admin_add_publication(): #εισαγωγή δημοσίευσης στη βάση από τον διαχειριστή
    doi = get_user_input("DOI: ")
    title = get_user_input("Τίτλος: ")
    language = get_user_input("Γλώσσα: ")
    summary = get_user_input("Περίληψη (προαιρετικό): ")
    url = get_user_input("URL (προαιρετικό): ")

    if not doi or not title or not language:
        show_error("DOI, Τίτλος και Γλώσσα είναι υποχρεωτικά.")
        return

    pub_type = get_user_input("Τύπος δημοσίευσης (1=Περιοδικό, 2=Συνέδριο): ")
    if pub_type == "1":
        pub_type = "Περιοδικό"
        extra_data = {
            "ISSN": get_user_input("ISSN: "),
            "Imer_dimosieysis": get_user_input("Ημερομηνία δημοσίευσης (YYYY-MM-DD): "),
            "Teyxos": get_user_input("Τεύχος: "),
            "Tomos": get_user_input("Τόμος: "),
            "Selides_periodikou": get_user_input("Σελίδες περιοδικού: "),
        }
        if not extra_data["ISSN"] or not extra_data["Imer_dimosieysis"]:
            show_error("ISSN και Ημερομηνία δημοσίευσης είναι υποχρεωτικά για Περιοδικό.")
            return

    elif pub_type == "2":
        pub_type = "Συνέδριο"
        extra_data = {
            "ISBN": get_user_input("ISBN: "),
            "Onoma_synedriou": get_user_input("Όνομα συνεδρίου: "),
            "Imer_dieksagogis": get_user_input("Ημερομηνία διεξαγωγής (YYYY-MM-DD): "),
            "Topos_dieksagogis": get_user_input("Τόπος διεξαγωγής: "),
        }
        if not extra_data["ISBN"] or not extra_data["Onoma_synedriou"]:
            show_error("ISBN και Όνομα συνεδρίου είναι υποχρεωτικά για Συνέδριο.")
            return

    else:
        show_error("Μη έγκυρος τύπος. Δώστε 1 ή 2.")
        return

    try:
        insert_publication(
            doi=doi,
            title=title,
            language=language,
            summary=summary or None,
            url=url or None,
            pub_type=pub_type,
            extra_data=extra_data
        )
        show_message("Η δημοσίευση προστέθηκε επιτυχώς.")

    except BackToMenu:
        raise
    except ValueError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"Σφάλμα κατά την προσθήκη: {e}")


def admin_update_publication(): #τροποποίηση τίτλου από τον διαχειριστή
    doi = get_user_input("Εισάγετε DOI δημοσίευσης για τροποποίηση: ")
    if not doi:
        show_error("Το DOI δεν μπορεί να είναι κενό.")
        return

    new_title = get_user_input("Εισάγετε νέο τίτλο: ")
    if not new_title:
        show_error("Ο νέος τίτλος δεν μπορεί να είναι κενός.")
        return

    try:
        update_pub_title(doi, new_title)
        show_message("Ο τίτλος ενημερώθηκε επιτυχώς.")

    except BackToMenu:
        raise
    except LookupError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"Σφάλμα κατά την τροποποίηση: {e}")

def admin_delete_publication(): #δθαγραφή δημοσίευσης από διαχειριστή
    doi = get_user_input("Εισάγετε DOI δημοσίευσης για διαγραφή: ")
    if not doi:
        show_error("Το DOI δεν μπορεί να είναι κενό.")
        return

    confirm = get_user_input(f"Θέλετε σίγουρα να διαγράψετε τη δημοσίευση {doi}; (ν/ο): ")
    if confirm != "ν":
        show_message("Ακύρωση διαγραφής.")
        return

    try:
        delete_publication(doi)
        show_message("Η δημοσίευση διαγράφηκε επιτυχώς.")

    except BackToMenu:
        raise
    except LookupError as e:
        show_error(str(e))
    except RuntimeError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"Σφάλμα κατά τη διαγραφή: {e}")

def admin_view_publications(): #προβολή όλων των δημοσιεύσεων από τον διαχειριστή
    try:
        pubs = get_all_publications()
        show_publications_list(pubs, title="Όλες οι δημοσιεύσεις")
    except Exception as e:
        show_error(f"Σφάλμα κατά την προβολή: {e}")

def admin_view_authors_and_institutions(): #προβολή όλων των συγγραφέων και ιδρυμάτων από τον διαχειριστή
    try:
        authors = get_all_authors()
        institutions = get_all_institutions()

        print("\n--- ΣΥΓΓΡΑΦΕΙΣ ---")
        if not authors:
            print("Δεν υπάρχουν συγγραφείς.")
        else:
            for a in authors:
                print(f"- {a['id_syggrafea']} | {a['Onomateponymo']}")

        print("\n--- ΙΔΡΥΜΑΤΑ ---")
        if not institutions:
            print("Δεν υπάρχουν ιδρύματα.")
        else:
            for i in institutions:
                print(f"- {i['id_idrymatos']} | {i['Onoma']} | {i['Dieythinsi']}")

    except Exception as e:
        show_error(f"Σφάλμα κατά την προβολή: {e}")

def admin_view_users():
    try:
        users = get_all_usernames()
        show_users(users)
    except Exception as e:
        show_error(f"Σφάλμα κατά την προβολή χρηστών: {e}")

def admin_delete_user(current_admin_username):
    try:
        users = get_all_usernames()
        show_users(users)

        username_to_delete = get_user_input("\nΔώστε το username που θέλετε να διαγράψετε: ")
        if not username_to_delete:
            show_error("Το username δεν μπορεί να είναι κενό.")
            return

        if username_to_delete == current_admin_username:
            show_error("Δεν μπορείτε να διαγράψετε τον εαυτό σας όσο είστε συνδεδεμένος.")
            return

        confirm = input(f"Θέλετε σίγουρα να διαγράψετε τον χρήστη '{username_to_delete}'; (ν/ο): ").strip().lower()
        if confirm != "ν":
            show_message("Ακύρωση διαγραφής χρήστη.")
            return

        delete_user_account(username_to_delete)
        show_message(f"Ο χρήστης '{username_to_delete}' διαγράφηκε επιτυχώς.")

    except BackToMenu:
        raise
    except LookupError as e:
        show_error(str(e))
    except Exception as e:
        show_error(f"Σφάλμα κατά τη διαγραφή χρήστη: {e}")

def admin_most_used_keyword_by_user():
    try:
        username = get_user_input("Δώστε username χρήστη: ")
        if not username:
            show_error("Το username δεν μπορεί να είναι κενό.")
            return

        result = get_most_used_keyword_for_user(username)
        show_most_used_keyword(username, result)

    except BackToMenu:
        raise    
    except Exception as e:
        show_error(f"Σφάλμα κατά την εκτέλεση ερωτήματος: {e}")

def admin_latest_comment():
    try:
        result = get_latest_comment_with_doi()
        show_latest_comment(result)
    except Exception as e:
        show_error(f"Σφάλμα κατά την ανάκτηση σχολίου: {e}")

def handle_user_choice(choice, username): #διαχείριση επιλογών χρήστη
    actions = {
        "1": lambda: show_general_subtree(username),
        "2": lambda: view_saved_pub_details(username),
        "3": lambda: add_publication(username),
        "4": lambda: delete_publication_from_folder(username),
        "5": lambda: new_folder(username),
        "6": lambda: delete_user_folder(username),
        "7": lambda: create_comment(username),
        "8": lambda: delete_user_comment(username),
        "9": lambda: show_comments_for_pub(username),
        "10": lambda: search_pub(),
        "11": lambda: search_pub_by_author(),
        "12": lambda: search_pub_by_keyword(),
    }
    action = actions.get(choice)
    if not action:
        show_error("Μη έγκυρη επιλογή.")
        return
    action()

def handle_admin_choice(choice, admin_username): #διαχείριση επιλογών διαχειριστή
    actions = {
        "1": admin_add_publication,
        "2": admin_update_publication,
        "3": admin_delete_publication,
        "4": admin_view_publications,
        "5": admin_view_authors_and_institutions,
        "6": admin_view_users,
        "7": lambda: admin_delete_user(admin_username),
        "8": admin_latest_comment,
        "9": admin_most_used_keyword_by_user,
    }
    action = actions.get(choice)
    if not action:
        show_error("Μη έγκυρη επιλογή.")
        return
    action()


def app_loop(): #loop μενού εφαρμογής
    while True:
        show_menu(starting_options, title="ΑΡΧΙΚΟ ΜΕΝΟΥ")
        choice = input("Επιλογή: ").strip()

        if choice == "0":
            print("Έξοδος από την εφαρμογή.")
            break

        if choice == "1": #σύνδεση
            user = sign_in()
            if not user:
                continue

            username = user["Username"]
            admin = user.get("Is_admin") == 1

            if admin:
                admin_loop(username)
            else:
                user_loop(username)

        elif choice == "2": #εγγραφή
            sign_up()

        else:
            show_error("Μη έγκυρη επιλογή.")


def user_loop(username):
    while True:
        show_menu(user_options, title=f"ΜΕΝΟΥ ΧΡΗΣΤΗ ({username})")
        choice = input("Επιλογή: ").strip()
        if choice == "0":
            print("Αποσύνδεση.")
            break

        try:
            handle_user_choice(choice, username)
        except BackToMenu:
            print("\n Επιστροφή στο μενού χρήστη...")
            continue


def admin_loop(username):
    while True:
        show_menu(admin_options, title=f"ΜΕΝΟΥ ADMIN ({username})")
        choice = input("Επιλογή: ").strip()
        if choice == "0":
            print("Αποσύνδεση.")
            break

        try:
            handle_admin_choice(choice, username)
        except BackToMenu:
            print("\n Επιστροφή στο μενού admin...")
            continue


if __name__ == "__main__":
    app_loop()

