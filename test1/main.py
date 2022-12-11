"""
Autor: Paweł Gorgolewski, student III roku Informatyki WIET

Poniższy szyfr blokowy działa dla klucza i wiadomości o długości 128 bitów
Dla reprodukowalności ustawiony został seed -> wszystkie tablice i SBOXy zawsze będą takie same, nie ma potrzeby
zapisywać ich ręcznie

Tworzenie podkluczy:
    Na 128 bitowy klucz aplikujemy PC1, PC2 oraz PC3. Każda z nich permutuje klucz oraz redukuje go odpowiednio do
    116, 108 i 100 bitów. Następnie wykonywane są 42 rundy polegające na:
        1. podzieleniu 100 bitowego klucza na połowę lewą i prawą
        2. wykonaniu rotacji w lewo o 1, 2, 3 lub 5 bitów
           (tablica SHIFT, gdzie indeks odpowiada ilości rotowanych bitów w danej rundzie)
        3. dodanie do tablicy podkluczy wartość połączonej lewej i prawej połówki po zastosowaniu PCK
           (PCK to permutacja z kompresją. Z 100 bitowego klucza tworzymy klucz o długości 88)

        Rezultat to 42 elementowa tablica zawierająca 88 bitowe podklucze

Funkcja nieliniowa:
    1. Rozszerzanie bloku:
        Otrzymując 64 bitowy blok, rozszerzamy go do 88 bitów przy użyciu EXPANSION_TABLE. Została ona zaprojektowana
        w taki sposób, aby żaden indeks nie powtórzył się po podzieleniu na 11 elementowe sekwencje

    2. XOR dla klucza oraz roszerzonego wcześniej bloku

    3.SBOX:
        Stworzono tablicę SBOXS posiadającą 8 SBOXów składających się z 64 wierszy i 32 kolumn każda. Wartości w SBOXach
        to liczby w przedziale 0-255. Jest to spowodowane tym, że przy podziale na 8 SBOXów, potrzebujemy 8 bitowe
        liczby, aby ostatecznie uzyskać 64 bitowy blok.

        Wiersz oraz kolumnę w sboxie otrzymujemy jako złożenie odpowiednio bitów na indeksach parzystych oraz
        nieparzystych wejścia 11 bitowego. Ostatecznie daje to 6 bitów na wiersz oraz 5 na kolumnę, co przekłada się
        na ilość wierszy oraz kolumn w SBOXach

    4. Ostateczna permutacja:
        Wynik sboxów (już 64 bitowy) podlega jeszcze ostatecznie podwójnej permutacji. Pierw przy użyciu
        FINAL_SBOX_PERMUTATION1, a następnie FINAL_SBOX_PERMUTATION2
"""
import random
import textwrap

random.seed(42)

# Zdefiniowanie długości tablic
KEY_LEN = 128
PC1_LEN = 116
PC2_LEN = 108
PC3_LEN = 100
PCK_LEN = 88
SHIFTS_LEN = 42
EXPANSION_LEN = PCK_LEN

# Generacja tablic PC -> najpierw lista [0,1,2,...,LEN_WCZESNIEJSZY-1], potem shuffle i obcięcie do pożądanej długości
PC1, PC2, PC3, PCK = [list(range(l)) for l in (KEY_LEN, PC1_LEN, PC2_LEN, PC3_LEN)]
random.shuffle(PC1)
random.shuffle(PC2)
random.shuffle(PC3)
random.shuffle(PCK)
PC1 = PC1[:PC1_LEN]
PC2 = PC2[:PC2_LEN]
PC3 = PC3[:PC3_LEN]
PCK = PCK[:PCK_LEN]

# Generacja tablicy SHIFTS -> SHIFTS_LEN razy losowana jest jedna z liczb: 1,2,3 lub 5
SHIFTS = random.choices([1, 2, 3, 5], k=SHIFTS_LEN)

# Tablicę EXPANSION_TABLE (o długości 88) przypisałem ręcznie, aby
# po podzieleniu na 11 elementowe sekwencje nie było powtórzeń
EXPANSION_TABLE = [
    36, 32, 49, 34, 5, 60, 38, 53, 29, 27, 1,
    6, 44, 14, 17, 8, 50, 26, 31, 25, 58, 7,
    47, 2, 61, 5, 41, 13, 40, 3, 10, 48, 12,
    28, 4, 59, 9, 51, 46, 6, 16, 63, 35, 56,
    29, 23, 11, 43, 30, 42, 1, 45, 55, 22, 18,
    21, 24, 19, 0, 20, 37, 62, 33, 54, 39, 52,
    22, 63, 43, 15, 6, 12, 57, 32, 9, 26, 1,
    8, 2, 37, 33, 28, 14, 51, 13, 10, 42, 55
]


# 8 sboxów bo tyle fragmentów klucza dostaniemy po podzieleniu na 11bitowe części
SBOXES_AMOUNT = 8
# Indeksy rzędów i kolumn to odpowiednio 6 oraz 5 bitowe liczby. Zakresy to 0-63 oraz 0-31 -> stąd takie długości
SBOX_ROW_LEN = 64
SBOX_COL_LEN = 32
# Wartości w sboxach w przedziale 0-255 (przekształcamy na liczbę 8 bitową)
SBOX_MAX_VAL = 255
SBOX_VAL_BINARY_LEN = 8
# Generacja SBOXÓW przy użyciu list comprehension oraz randint(<min_val>, <max_val>)
SBOXS = [
    [
        [
            random.randint(0, SBOX_MAX_VAL) for _ in range(SBOX_COL_LEN)
        ] for _ in range(SBOX_ROW_LEN)
    ] for _ in range(SBOXES_AMOUNT)
]

# Generacja tablic do permutacji po sboxach -> tak jak generacja tablic PC ale bez obcięcia
FINAL_SBOX_PERMUTATION1 = list(range(KEY_LEN // 2))
FINAL_SBOX_PERMUTATION2 = list(range(KEY_LEN // 2))
random.shuffle(FINAL_SBOX_PERMUTATION1)
random.shuffle(FINAL_SBOX_PERMUTATION2)


def apply_permutation(key: str, pc_table: list[int]):
    result = ""
    for index in pc_table:
        result += key[index]
    return result


def split_in_half(s: str):
    return s[0: len(s) // 2], s[len(s) // 2:]


def shift_left(s: str, shift_num: int):
    return s[shift_num:] + s[:shift_num]


def XOR(bits1: str, bits2: str):
    return "".join("0" if bits1[i] == bits2[i] else "1" for i in range(len(bits1)))


def apply_initial_pcs(key_128: str):
    key_116 = apply_permutation(key_128, PC1)
    key_108 = apply_permutation(key_116, PC2)
    return apply_permutation(key_108, PC3)


def generate_keys(key_128: str):
    round_keys = list()

    key_100 = apply_initial_pcs(key_128)
    for round_shift in SHIFTS:
        l, r = split_in_half(key_100)
        l, r = shift_left(l, round_shift), shift_left(r, round_shift)
        round_keys.append(apply_permutation(l + r, PCK))

    return round_keys


def generate_11bits_list(key: str):
    return textwrap.wrap(key, 11)


def apply_expansion(key: str):
    bits88 = ""
    for index in EXPANSION_TABLE:
        bits88 += key[index]
    return bits88


def get_sbox_cords(key: str) -> tuple[int, int]:
    """Zwraca row, col -> row to bity na parzystych indexach, col na nieparzystych"""
    row, col = "", ""
    for i, bit in enumerate(key):
        if i % 2 == 0:
            row += bit
        else:
            col += bit

    return int(row, 2), int(col, 2)


get_bin = lambda x, n: format(x, 'b').zfill(n)


def apply_final_sbox_permutations(key: str):
    key_after_first_permutation = apply_permutation(key, FINAL_SBOX_PERMUTATION1)
    return apply_permutation(key_after_first_permutation, FINAL_SBOX_PERMUTATION2)


def f_function(pre64, key88):
    final64 = ''
    block88 = apply_expansion(pre64)
    xored_block = XOR(block88, key88)
    for sbox_id, chunk in enumerate(generate_11bits_list(xored_block)):
        row, col = get_sbox_cords(chunk)
        sbox_val = SBOXS[sbox_id][row][col]
        final64 += get_bin(sbox_val, SBOX_VAL_BINARY_LEN)

    return apply_final_sbox_permutations(final64)


def encrypt(message, key):
    l, r = split_in_half(message)
    for subkey in generate_keys(key):
        l, r = r, XOR(f_function(r, subkey), l)

    return r + l


def decrypt(message, key):
    l, r = split_in_half(message)
    for subkey in reversed(generate_keys(key)):
        l, r = r, XOR(f_function(r, subkey), l)

    return r + l


def intoIntArray(message: str):
    int_array = []
    mesg_array = list(message)
    for i in mesg_array:
        int_array.append(ord(i))
    return int_array


def intoCharArray(message: []):
    mesg_char = []
    for i in message:
        mesg_char.append(chr(i))
    return mesg_char


def intListToBinStr(message_list):
    binary = []
    for x in message_list:
        binary.append(get_bin(x, 8))
    binary_str = ""
    for x in binary:
        binary_str += x
    return binary_str


if __name__ == '__main__':
    message = "HelloMyMesIsThis"
    key = "!MySuperKeyIsTheBestKeyEver!"

    plaintext = intListToBinStr(intoIntArray(message))
    print("Plaintext (128 bits):", plaintext)
    binary_key = intListToBinStr(intoIntArray(key))
    bin128key = binary_key[:128]
    print("Key (only 128 bits): ", bin128key)

    ciphertext = encrypt(plaintext, bin128key)
    print("Ciphertext:          ", ciphertext)
    decrypted = decrypt(ciphertext, bin128key)
    print("Encrypted message:   ", decrypted)

    assert plaintext == decrypted, "plaintext is different than decrypted!"
    print("Working correctly :)")
