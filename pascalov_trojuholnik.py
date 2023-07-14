import tkinter as tk

def pascal_triangle(n):
  # Vytvorime 2D maticu pre ulozenie hodnot
  triangle = [[1] * (i + 1) for i in range(n)]

  # Prechadzame maticu a vypocitame hodnoty pre vsetky riadky
  # okrem prveho, pretoze prvy riadok uz ma vsetky hodnoty nastavene na 1
  for i in range(1, n):
    for j in range(1, i):
      # Hodnoty v Pascalovom trojuholniku sa vypocitavaju
      # ako súčet hodnôt z predchádzajúceho riadku
      triangle[i][j] = triangle[i-1][j-1] + triangle[i-1][j]

  # Vratime maticu s hodnotami
  return triangle

# Vytvorime okno a canvas pre vykreslenie trojuholnika
window = tk.Tk()
canvas = tk.Canvas(window, width=500, height=500)
canvas.pack()

# Definujeme premennu n
n = 64

# Vypocitame krok pre vykreslenie trojuholnika na ploche canvasu
step = 500 // (n + 1)

# Prechadzame maticu s hodnotami trojuholnika a vykreslime hodnoty na canvas
for i, row in enumerate(pascal_triangle(n)):
  for j, value in enumerate(row):
    # Vypocitame poziciu pre vykreslenie hodnoty
    x = step * (j + 1)
    y = step * (i + 1)
    # Vypocitame horizontalne posunutie hodnoty v zavislosti od sirky canvasu a poctu hodnot v riadku
    shift = (500 - step * len(row)) // 2
    # Vyberieme farbu textu v zavislosti od parosti hodnoty
    if value % 2 == 0:
      color = 'lightgray'
    else:
      color = 'black'
    # Vykreslime hodnotu na canvas
    #canvas.create_text(x + shift, y, text=str(value))
    canvas.create_oval(x + shift - 2, y - 2, x + shift + 2, y + 2, fill=color, outline=color)

# Spustime hlavny event loop
window.mainloop()
