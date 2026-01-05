import sqlite3
import hashlib
DB_NAME = "PublicationsDB.db" 

def get_connection():
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA foreign_keys = ON;")
    return con

#Λειτουργίες δημοσιεύσεων

def get_all_publications(): #προβολή όλων των δημοσιεύσεων που υπάρχουν στη βάση
    publications=[]
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("""
            SELECT DOI, Titlos, Glossa, Imer_prosthikis, Perilipsi, URL
            FROM DIMOSIEYSI
            ORDER BY Imer_prosthikis DESC;
        """)
        colnames=[d[0] for d in cur.description]
        for row in cur.fetchall():
            publications.append(dict(zip(colnames, row)))
    return publications

def get_saved_publications(username): #επιστρέφει τις αποθηκευμένες δημοσιεύσεις του χρήστη (ανεξάρτητα από φάκελο)
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT DISTINCT D.DOI, D.Titlos
            FROM DIMOSIEYSI D
            JOIN XRHSTHS_APOTHIK_DIMOS_SE_FAKELO X ON D.DOI = X.DOI_dim
            WHERE X.Username = ?
            ORDER BY D.Titlos;
        """, (username,))
        rows = cur.fetchall()
        return [{"DOI": doi, "Titlos": title} for doi, title in rows]


def get_folder_publications_details(folder_id, username): #Επιστρέφει δημοσιεύσεις που υπάρχουν σε συγκεκριμένο φάκελο χρήστη
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT D.DOI, D.Titlos, D.Glossa, D.Imer_prosthikis, D.URL
            FROM XRHSTHS_APOTHIK_DIMOS_SE_FAKELO AS X
            JOIN DIMOSIEYSI AS D ON D.DOI = X.DOI_dim
            WHERE X.id_fakelou = ? AND X.Username = ?
            ORDER BY D.Imer_prosthikis DESC;
        """, (folder_id, username))
        rows = cur.fetchall()
        if not rows:
            return []
        colnames = [d[0] for d in cur.description]
        return [dict(zip(colnames, r)) for r in rows]


def insert_publication(doi, title, language, summary, url, pub_type, extra_data): #εισαγωγή δημοσίευσης
    with get_connection() as con:
        cur=con.cursor()
        try:
            cur.execute("""
                INSERT INTO DIMOSIEYSI (DOI, Titlos, Glossa, Imer_prosthikis, Perilipsi, URL)
                VALUES (?, ?, ?, DATE('now'), ?, ?);
            """, (doi, title, language, summary, url))
            if pub_type=="Περιοδικό":
                cur.execute("""INSERT INTO ARTHRO_SE_PERIODIKO (DOI_dimosieysis, ISSN, Imer_dimosieysis, Teyxos, Tomos, Selides_periodikou)
                            VALUES (?, ?, ?, ?, ?, ?);
                            """, (doi, extra_data['ISSN'], extra_data['Imer_dimosieysis'], extra_data['Teyxos'], extra_data['Tomos'], extra_data['Selides_periodikou']))
            elif pub_type=="Συνέδριο":
                cur.execute("""INSERT INTO ARTHRO_SE_SYNEDRIO (DOI_dimosieysis, ISBN, Onoma_synedriou, Imer_dieksagogis, Topos_dieksagogis)
                            VALUES (?, ?, ?, ?, ?);
                            """, (doi, extra_data['ISBN'], extra_data['Onoma_synedriou'], extra_data['Imer_dieksagogis'], extra_data['Topos_dieksagogis']))
            con.commit()
            return True
        except sqlite3.Error as e:
            con.rollback()
            raise ValueError(f"Αποτυχία εισαγωγής: {e}")
        
def delete_publication(doi): #διαγραφή δημοσίευσης
    with get_connection() as con: 
        cur = con.cursor()
        try:
            cur.execute("DELETE FROM DIMOSIEYSI WHERE DOI=?;", (doi,))
            if cur.rowcount==0:
                raise LookupError("Δεν βρέθηκε δημοσίευση με αυτό το DOI")
            con.commit()
        except sqlite3.IntegrityError as e:
            raise RuntimeError("Δεν είναι δυνατή η διαγραφή: υπάρχουν σχετικές αναφορές.") from e

def get_publication_by_doi(doi): #επιστρέφει στοιχεία δημοσίευσης με βάση το DOI
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT DOI, Titlos, Glossa, Imer_prosthikis, Perilipsi, URL
            FROM DIMOSIEYSI
            WHERE DOI = ?;
        """, (doi,))
        row = cur.fetchone()
        if not row:
            return None
        colnames = [d[0] for d in cur.description]
        return dict(zip(colnames, row))

def get_pub_type(doi): #επιστρέφει τον τύπο της δημοσίευσης
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("SELECT 1 FROM ARTHRO_SE_PERIODIKO WHERE DOI_dimosieysis=?", (doi,))
        if cur.fetchone():
            return "Περιοδικό"
        cur.execute("SELECT 1 FROM ARTHRO_SE_SYNEDRIO WHERE DOI_dimosieysis=?", (doi,))
        if cur.fetchone():
            return "Συνέδριο"
        return "Άγνωστο"
    
def get_detailed_pub_info(doi, pub_type): #επιστρέφει λεπτομέρειες ανάλογα με τον τύπο της δημοσίευσης
    with get_connection() as con:
        cur=con.cursor()
        if pub_type=="Περιοδικό":
            cur.execute("SELECT ISSN, Imer_dimosieysis, Teyxos, Tomos, Selides_periodikou FROM ARTHRO_SE_PERIODIKO WHERE DOI_dimosieysis=?", (doi,))
        elif pub_type=="Συνέδριο":
            cur.execute("SELECT ISBN, Onoma_synedriou, Imer_dieksagogis, Topos_dieksagogis FROM ARTHRO_SE_SYNEDRIO WHERE DOI_dimosieysis=?", (doi,))
        row=cur.fetchone()
        if row:
            colnames=[d[0] for d in cur.description]
            return dict(zip(colnames, row))
        return {}

#Λειτουργίες συγγραφέων

def get_all_authors(): #προβολή όλων των συγγραφέων
    authors=[]
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("""
            SELECT id_syggrafea, Onomateponymo
            FROM SYGGRAFEAS
            ORDER BY Onomateponymo;
        """)
        colnames=[d[0] for d in cur.description]
        for row in cur.fetchall():
            authors.append(dict(zip(colnames, row)))
    return authors

def insert_author(fullname): #εισαγωγή συγγραφέα
    with get_connection() as con:
        cur=con.cursor()
        try:
            cur.execute("""
                INSERT INTO SYGGRAFEAS (Onomateponymo)
                VALUES (?);
            """, (fullname,))
            con.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError("Αποτυχία εισαγωγής συγγραφέα. Το όνομα υπάρχει ήδη.")

def get_authors_from_publication(doi): #συγγραφείς μιας δημοσίευσης
    authors_pub=[]
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("""
            SELECT Onomateponymo FROM SYSXETISI_SYGGR_DIMOS_IDR AS s1
            JOIN SYGGRAFEAS AS s2 ON s1.id_syggrafea=s2.id_syggrafea
            WHERE s1.DOI_dimosieysis=?;
        """, (doi,))
        colnames=[d[0] for d in cur.description]
        for row in cur.fetchall():
            authors_pub.append(dict(zip(colnames, row)))
    return authors_pub

def link_author_to_publication(author_id, doi, id_idrymatos): #συσχέτιση συγγραφέα με δημοσίευση
    with get_connection() as con:
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO SYSXETISI_SYGGR_DIMOS_IDR (id_syggrafea, DOI_dimosieysis, id_idrymatos)
                VALUES (?, ?, ?);
            """, (author_id, doi, id_idrymatos))
            con.commit()
        except sqlite3.IntegrityError as e:
            pass #αν υπάρχει ήδη η σύνδεση
        except Exception as e:
            raise RuntimeError(f"Σφάλμα σύνδεσης συγγραφέα με δημοσίευση: {e}") from e

def get_all_institutions(): #προβολή όλων των ιδρυμάτων που υπάρχουν στη βάση
    institutions=[]
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("""
            SELECT id_idrymatos, Onoma, Dieythinsi
            FROM IDRYMA
            ORDER BY id_idrymatos;
        """)
        colnames=[d[0] for d in cur.description]
        for row in cur.fetchall():
            institutions.append(dict(zip(colnames, row)))
    return institutions

#Λειτουργίες λέξεων-κλειδιών

def get_keywords_for_publication(doi): #επιστρέφει τις λέξεις-κλειδιά μιας δημοσίευσης
    keywords = []
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT lk.keyword
            FROM DIMOS_EXEI_LEKSEIS_KLEIDIA AS d
            JOIN LEKSI_KLEIDI AS lk ON d.id_leksis = lk.keyword_id
            WHERE d.DOI_dimosieysis = ?;
        """, (doi,))
        colnames = [d[0] for d in cur.description]
        for row in cur.fetchall():
            keywords.append(dict(zip(colnames, row)))
    return keywords


def get_keyword_id(keyword):   #επιστρέφει το id μιας λέξης-κλειδί
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("""
        SELECT keyword_id FROM LEKSI_KLEIDI
        WHERE keyword=?;
    """, (keyword,))
        row=cur.fetchone()
        return row[0] if row else None

def insert_new_keyword(keyword): #εισαγωγή λέξης-κλειδιού στη βάση
    with get_connection() as con:
        cur=con.cursor()
        try:
            cur.execute("INSERT INTO LEKSI_KLEIDI (keyword) VALUES (?)", (keyword,))
            con.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return get_keyword_id(keyword)     
   
def insert_keyword(doi, keyword): #προσθήκη λέξης-κλειδί σε δημοσίευση, αποθηκεύει τη λέξη αν δεν υπάρχει
    keyword=keyword.strip()
    if not keyword:
        return
    keyword_id=insert_new_keyword(keyword)
    if keyword_id is None:
        keyword_id=insert_new_keyword(keyword)

    with get_connection() as con:
        cur=con.cursor()
        try:
            cur.execute("""
                        INSERT INTO DIMOS_EXEI_LEKSEIS_KLEIDIA (DOI_dimosieysis, id_leksis)
                        VALUES (?, ?);
                        """, (doi, keyword_id))
            con.commit()
        except sqlite3.IntegrityError:
            pass #η σύνδεση υπάρχει ήδη
        except Exception as e:
             raise RuntimeError(f"Σφάλμα σύνδεσης λέξης-κλειδί με δημοσίευση: {e}") from e
        
def get_most_used_keyword_for_user(username): #επιστρέφει τη λέξη-κλειδί που εμφανίζεται στα περισσότερα αποθηκευμένα άρθρα ενός χρήστη
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT l.keyword, COUNT(*) AS plithos
            FROM XRHSTHS_APOTHIK_DIMOS_SE_FAKELO AS x
            JOIN DIMOSIEYSI AS d
              ON x.DOI_dim = d.DOI
            JOIN DIMOS_EXEI_LEKSEIS_KLEIDIA AS lk
              ON d.DOI = lk.DOI_dimosieysis
            JOIN LEKSI_KLEIDI AS l
              ON lk.id_leksis = l.keyword_id
            WHERE x.Username = ?
            GROUP BY l.keyword
            ORDER BY plithos DESC
            LIMIT 1;
        """, (username,))

        row = cur.fetchone()
        if not row:
            return None

        return {
            "keyword": row[0],
            "plithos": row[1]
        }


#Λειτουργίες αναζήτησης/φιλτραρίσματος

def search_publications(word): #αναζήτηση δημοσίευσης με βάση τίτλο ή DOI
    word_pattern = f"%{word}%"
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT DISTINCT DOI, Titlos, Glossa, Imer_prosthikis, Perilipsi, URL
            FROM DIMOSIEYSI
            WHERE Titlos LIKE ? OR DOI LIKE ?
            ORDER BY Titlos;
        """, (word_pattern, word_pattern))
        rows = cur.fetchall()
        if not rows:
            return []
        colnames = [d[0] for d in cur.description]
        return [dict(zip(colnames, r)) for r in rows]

    
def search_authors(name):  #αναζήτηση συγγραφέα με βάση ονοματεπώνυμο
    word_pattern = f"%{name}%"
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT id_syggrafea, Onomateponymo
            FROM SYGGRAFEAS
            WHERE Onomateponymo LIKE ?
            ORDER BY Onomateponymo;
        """, (word_pattern,))
        rows = cur.fetchall()
        colnames = [d[0] for d in cur.description]
        return [dict(zip(colnames, r)) for r in rows]

def get_pubs_by_author(author_id):  #επιστρέφει τις δημοσιεύσεις ενός συγγραφέα
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT D.DOI, D.Titlos, D.Glossa, D.Imer_prosthikis, D.Perilipsi, D.URL
            FROM DIMOSIEYSI AS D
            JOIN SYSXETISI_SYGGR_DIMOS_IDR AS S ON D.DOI = S.DOI_dimosieysis
            WHERE S.id_syggrafea = ?
            ORDER BY D.Imer_prosthikis DESC;
        """, (author_id,))
        rows = cur.fetchall()
        colnames = [d[0] for d in cur.description]
        return [dict(zip(colnames, r)) for r in rows]
    
def get_pubs_by_keyword(keyword): #επιστρέφει τις δημοσιεύσεις που σχετίζονται με μια λέξη-κλειδί
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("""SELECT DISTINCT D.DOI, D.Titlos, D.Glossa, D.Imer_prosthikis, D.URL
                    FROM DIMOSIEYSI AS D
                    JOIN DIMOS_EXEI_LEKSEIS_KLEIDIA AS E ON D.DOI=E.DOI_dimosieysis
                    JOIN LEKSI_KLEIDI AS LK ON E.id_leksis=LK.keyword_id
                    WHERE LK.keyword LIKE ?;
                    """, (f'%{keyword}%',))
        rows=cur.fetchall()
        if not rows:
            return []
        colnames=[d[0] for d in cur.description]
        return [dict(zip(colnames, row)) for row in rows]
    
def update_pub_title(doi, new_title): #τροποποίηση τίτλου δημοσίευσης
    with get_connection() as con:
        cur=con.cursor()
        cur.execute("""
            UPDATE DIMOSIEYSI 
            SET Titlos=? 
            WHERE DOI=?;
            """, (new_title, doi))
        if cur.rowcount==0:
            raise LookupError("Δεν βρέθηκε δημοσίευση με αυτό το DOI")
        con.commit()

def update_username(old_username, new_username): #τροποποίηση username
    with get_connection() as con:
        cur=con.cursor()
        try:
            cur.execute("SELECT Username FROM XRHSTHS WHERE Username=?", (new_username,))
            if cur.fetchone():
                raise ValueError("Το νέο username χρησιμοποιείται ήδη από άλλο χρήστη")
            cur.execute("""
                UPDATE XRHSTHS 
                SET Username=? 
                WHERE Username=?;
                """, (new_username, old_username))
            con.commit()
            return True
        except sqlite3.Error as e:
            print(f"Σφάλμα κατά την αλλαγή username: {e}")
            con.rollback()
            return False
        except ValueError as e:
            print(e)
            return False
    
#Λειτουργίες σχολίων
    
def get_comments_by_pub_and_user(doi, username): #επιστρέφει σχόλια του χρήστη σε μια δημοσίευση
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT S.id_sxoliou,
                   S.Periexomeno,
                   S.Imer_dimiourgias
            FROM SXOLIO AS S
            JOIN PROSTHIKI_SXOLIOU_SE_DIMOSIEYSI AS P
                 ON S.id_sxoliou = P.id_sxoliou
            WHERE P.DOI_dimosieysis = ?
              AND P.Username = ?
            ORDER BY S.Imer_dimiourgias DESC;
        """, (doi, username))

        rows = cur.fetchall()
        if not rows:
            return []

        colnames = [d[0] for d in cur.description]
        return [dict(zip(colnames, row)) for row in rows]

    
def insert_comment_to_pub(doi, username, text): #προσθήκη σχολίου σε δημοσίευση
    with get_connection() as con:
        cur=con.cursor()
        try:
            cur.execute("""
                INSERT INTO SXOLIO (Periexomeno, Imer_dimiourgias)
                VALUES (?, DATE('now'));
            """, (text,))
            last_comment_id=cur.lastrowid
            cur.execute("""
                INSERT INTO PROSTHIKI_SXOLIOU_SE_DIMOSIEYSI (id_sxoliou, Username, DOI_dimosieysis)
                VALUES (?, ?, ?);
                        """, (last_comment_id, username, doi))
            con.commit()
        except sqlite3.IntegrityError as e:
            raise ValueError("Αποτυχία εισαγωγής σχολίου.")
            con.rollback() #ακύρωση αλλαγών σε περίπτωση σφάλματος

def delete_comment(comment_id, username): #διαγραφή σχολίου
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT 1
            FROM PROSTHIKI_SXOLIOU_SE_DIMOSIEYSI
            WHERE id_sxoliou = ? AND Username = ?;
        """, (comment_id, username))
        if not cur.fetchone():
            raise LookupError("Δεν βρέθηκε σχόλιο για αυτόν τον χρήστη.")

        cur.execute("""
            DELETE FROM PROSTHIKI_SXOLIOU_SE_DIMOSIEYSI
            WHERE id_sxoliou = ? AND Username = ?;
        """, (comment_id, username))

        cur.execute("DELETE FROM SXOLIO WHERE id_sxoliou = ?;", (comment_id,))
        con.commit()
        return True

def get_latest_comment_with_doi(): #επιστρέφει το πιο πρόσφατο σχόλιο μαζί με username, DOI, περιεχόμενο
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT p.Username,
                   p.DOI_dimosieysis,
                   s.Imer_dimiourgias,
                   s.Periexomeno
            FROM SXOLIO s
            JOIN PROSTHIKI_SXOLIOU_SE_DIMOSIEYSI p
              ON p.id_sxoliou = s.id_sxoliou
            ORDER BY s.Imer_dimiourgias DESC
            LIMIT 1;
        """)

        row = cur.fetchone()
        if not row:
            return None

        return {
            "Username": row[0],
            "DOI": row[1],
            "Imer_dimiourgias": row[2],
            "Periexomeno": row[3]
        }

#Λειτουργίες φακέλων

def get_or_create_folder(name, username, parent_id=None): #επιστρέφει ή δημιουργεί φάκελο

    with get_connection() as con:
        cur = con.cursor()

        if parent_id is None:
            cur.execute("""
                SELECT id_fakelou
                FROM FAKELOS
                WHERE Onoma = ?
                  AND Username = ?
                  AND id_kyriou_fakelou IS NULL;
            """, (name, username))
        else:
            cur.execute("""
                SELECT id_fakelou
                FROM FAKELOS
                WHERE Onoma = ?
                  AND Username = ?
                  AND id_kyriou_fakelou = ?;
            """, (name, username, parent_id))

        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute("""
            INSERT INTO FAKELOS (Onoma, Username, id_kyriou_fakelou, Megethos)
            VALUES (?, ?, ?, 0);
        """, (name, username, parent_id))
        con.commit()
        return cur.lastrowid

def get_folder_parent_id(folder_id, username): #επιστρέφει το id του κύριου φακέλου
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT id_kyriou_fakelou
            FROM FAKELOS
            WHERE id_fakelou = ? AND Username = ?;
        """, (folder_id, username))
        row = cur.fetchone()
        return row[0] if row else None

def is_in_general_subtree(folder_id, general_id, username): #ελέγχει ότι ο φάκελος είναι μέσα στον γενικό φάκελο
    current = folder_id
    while current is not None:
        if current == general_id:
            return True
        current = get_folder_parent_id(current, username)
    return False


def add_pub_to_folder(doi, folder_id, username): #προσθήκη δημοσίευσης σε φάκελο
    if folder_id is None:
        raise ValueError("Πρέπει να οριστεί ένας έγκυρος φάκελος.")
        
    with get_connection() as con:
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO XRHSTHS_APOTHIK_DIMOS_SE_FAKELO (Username, DOI_dim, id_fakelou)
                VALUES (?, ?, ?)
            """, (username, doi, folder_id))
            con.commit()
        except sqlite3.IntegrityError:
            pass

def remove_pub_from_folder(doi, folder_id, username): #αφαίρεση δημοσίευσης από φάκελο
    with get_connection() as con: 
        cur = con.cursor()
        try:
            cur.execute("""DELETE FROM XRHSTHS_APOTHIK_DIMOS_SE_FAKELO
                        WHERE DOI_dim=? AND id_fakelou=? AND Username=?
                        """, (doi, folder_id, username))
            if cur.rowcount==0:
                raise LookupError("Η δημοσίευση δεν βρέθηκε στον συγκεκριμένο φάκελο.")
            con.commit()
            return True
        except sqlite3.Error as e:
            print(f"Σφάλμα κατά την αφαίρεση από τον φάκελο: {e}")
            con.rollback()       

def get_user_folders(username): #επιστρέφει τους φακέλους του χρήστη
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT id_fakelou, id_kyriou_fakelou, Onoma, Megethos
            FROM FAKELOS
            WHERE Username=?
            ORDER BY Onoma;
        """, (username,))
        rows = cur.fetchall()
        if not rows:
            return []
        colnames = [d[0] for d in cur.description]
        return [dict(zip(colnames, r)) for r in rows]

    
def get_subfolders(folder_id, username): #επιστρέφει τους υποφακέλους του χρήστη
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT id_fakelou, Onoma
            FROM FAKELOS
            WHERE id_kyriou_fakelou = ? AND Username = ?
            ORDER BY Onoma;
        """, (folder_id, username))
        return cur.fetchall()


def delete_folder(folder_id, username): #διαγραφή φακέλου
    with get_connection() as con:
        cur = con.cursor()
        try:
            cur.execute("""
                DELETE FROM XRHSTHS_APOTHIK_DIMOS_SE_FAKELO
                WHERE id_fakelou = ? AND Username = ?
            """, (folder_id, username))

            cur.execute("""
                DELETE FROM FAKELOS
                WHERE id_fakelou = ? AND Username = ?
            """, (folder_id, username))

            if cur.rowcount == 0:
                raise LookupError("Δεν βρέθηκε ο φάκελος.")

            con.commit()
            return True

        except sqlite3.Error as e:
            con.rollback()
            raise ValueError("Σφάλμα κατά τη διαγραφή του φακέλου.") from e


#Λειτουργίες χρηστών

def hash_password(password): #επιστρέφει το hash του κωδικού
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def new_user(username, email, fullname, password): #εγγραφή νέου χρήστη
    hashed_password=hash_password(password)
    with get_connection() as con:
        cur=con.cursor()
        try:
            cur.execute("""
                INSERT INTO XRHSTHS (Username, email, Onomateponymo, Password)
                VALUES (?, ?, ?, ?);
                """, (username, email, fullname, hashed_password))
            con.commit()
            return True
        except sqlite3.IntegrityError as e:
            if "Username" in str(e):
                raise ValueError("Το username χρησιμοποιείται ήδη") from e
            if "email" in str(e):
                raise ValueError("Το email χρησιμοποιείται ήδη") from e
            raise ValueError("Αποτυχία εγγραφής χρήστη") from e

def delete_user_account(username): #διαγραφή χρήστη και δεδομένων που σχετίζονται με το username
    if not username:
        raise ValueError("Το username δεν μπορεί να είναι κενό.")

    with get_connection() as con:
        cur = con.cursor()
        try:
            cur.execute("SELECT 1 FROM XRHSTHS WHERE Username = ?;", (username,))
            if not cur.fetchone():
                raise LookupError("Δεν βρέθηκε χρήστης με αυτό το username.")

            cur.execute("""
                DELETE FROM XRHSTHS_APOTHIK_DIMOS_SE_FAKELO
                WHERE Username = ?;
            """, (username,))

            cur.execute("""
                DELETE FROM PROSTHIKI_SXOLIOU_SE_DIMOSIEYSI
                WHERE Username = ?;
            """, (username,))

            while True:
                cur.execute("""
                    DELETE FROM FAKELOS
                    WHERE Username = ?
                      AND id_fakelou NOT IN (
                          SELECT DISTINCT id_kyriou_fakelou
                          FROM FAKELOS
                          WHERE Username = ? AND id_kyriou_fakelou IS NOT NULL
                      );
                """, (username, username))
                if cur.rowcount == 0:
                    break

            cur.execute("DELETE FROM XRHSTHS WHERE Username = ?;", (username,))

            con.commit()
            return True

        except Exception:
            con.rollback()
            raise


def verify_user(username, password): #επαλήθευση χρήστη
    user=get_user_by_username(username)
    if not user:
        return None
    hashed_input=hash_password(password)
    if user['Password']==hashed_input: #συγκρίνει τον hashed κωδικό που δίνει ο χρήστης με τον αποθηκευμένο
        del user['Password'] #αφαιρώ τον κωδικό πριν επιστρέψω τα στοιχεία του χρήστη
        return user
    return None

def get_user_by_username(username): #επιστρέφει τα στοιχεία χρήστη
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT Username, email, Onomateponymo, Password, Is_admin
            FROM XRHSTHS 
            WHERE Username = ?;
        """, (username,))
        row = cur.fetchone()
        if not row:
            return None
        colnames = [d[0] for d in cur.description]
        return dict(zip(colnames, row))
    
def get_all_usernames(): #επιστρέφει λίστα με όλα τα usernames
    with get_connection() as con:
        cur = con.cursor()
        cur.execute("""
            SELECT Username, Is_admin
            FROM XRHSTHS
            ORDER BY Username;
        """)
        rows = cur.fetchall()
        if not rows:
            return []
        return [{"Username": r[0], "Is_admin": r[1]} for r in rows]

def is_admin(username): #ελέγχει αν ένας χρήστης είναι διαχειριστής
    user = get_user_by_username(username)
    return user is not None and user.get('Is_admin') == 1