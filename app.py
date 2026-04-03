from flask import Flask, render_template, request
import plotly.graph_objs as go
from plotly.subplots import make_subplots

app = Flask(__name__)

previous_trace_temp = None
previous_trace_P = None
V = None
kp = None
Ti = None
temperature = None
zad_temperature = None

@app.route("/", methods=["GET", "POST"])
def index():
    global previous_trace_temp, previous_trace_P, V, kp, Ti, temperature, zad_temperature
    graph_html = None
    prev_V = V 

    if request.method == "POST":
        V = float(request.form.get("volume", V))
        kp = float(request.form.get("kp", kp))
        temperature = float(request.form.get("temperature", temperature))
        zad_temperature = float(request.form.get("zad_temperature", zad_temperature))
        Ti = float(request.form.get("Ti", Ti))
        print("Received values:", "V:", V, "kp:", kp, "temperature:", temperature, "zad_temperature: ", zad_temperature, "Ti: ", Ti)

        if V != prev_V:
            previous_trace_temp = None
            previous_trace_P = None

        if V == 50:
            t_sim, Tp, P_max, Kc = 5000.0, 0.5, 4000, 250.0
        elif V == 100:
            t_sim, Tp, P_max, Kc = 10000.0, 2.0, 8000, 350.0
        elif V == 500:
            t_sim, Tp, P_max, Kc = 15000.0, 5.0, 20000, 700.0
        elif V == 1000:
            t_sim, Tp, P_max, Kc = 25000.0, 10.0, 20000, 1000.0
        elif V == 10000:
            t_sim, Tp, P_max, Kc = 50000.0, 50.0, 70000, 3500.0
        N = int(t_sim / Tp) + 1

        Cv = 1005 * 1.2 * V

        Temp_zew = temperature + 273.15
        Temp_min = Temp_zew
        Temp_zad = zad_temperature + 273.15
        Temp_max = Temp_zad + 5


        U_min = 0
        U_max = 1
        P_min = 0.1

        e_n = 0
        e_sum = 0

        temp = [Temp_min]
        t = [0.0]
        P = []
        U = []

        for i in range(N):
            e_n = Temp_zad - temp[i]
            e_sum += e_n
            u_pi_n = kp * (e_n + (Tp / Ti) * e_sum)
            u_n = min(1, max(0, u_pi_n)) 
            U.append(u_n)
            P.append((P_max - P_min) / (U_max - U_min) * (u_n - U_min) + P_min)

            temp_new = ((P[i] - Kc * (temp[i] - Temp_zew))) / Cv * Tp + temp[i]
            temp.append(min(Temp_max, max(Temp_min, temp_new)))
            
            t.append((i + 1) * Tp)
        
        for i in range(len(temp)):
            temp[i] -= 273.15
            t[i] = round(t[i]/60, 1)
        Temp_zad = Temp_zad - 273.15
      
        fig = make_subplots(rows=2, cols=1, subplot_titles=(
            "Zależność temperatury od czasu",
            "Zależność mocy grzewczej P od czasu"
        ))
        current_trace_temp = go.Scatter(x=t, y=temp, mode='lines', name='T(t)', line=dict(color='#1074f8'), hovertemplate='Czas: %{x} min<br>Temperatura: %{y:.1f} °C')
        current_trace_P = go.Scatter(x=t[:-1], y=P, mode='lines', name='P(t)', line=dict(color='#1074f8'), hovertemplate='Czas: %{x} min<br>Moc: %{y:.1f} W')
        
        if previous_trace_temp and previous_trace_P:
            previous_trace_temp.line.width = 2
            fig.add_trace(previous_trace_temp, row=1, col=1)
            previous_trace_P.line.width = 2
            fig.add_trace(previous_trace_P, row=2, col=1)

        current_trace_temp = go.Scatter(
            x=t, y=temp, mode='lines', name='T(t) - aktualny',
            line=dict(color='white', width=2), hovertemplate='Czas: %{x} min<br>Temperatura: %{y:.1f} °C'
        )
        current_trace_P = go.Scatter(
            x=t[:-1], y=P, mode='lines', name='P(t) - aktualny',
            line=dict(color='white', width=2), hovertemplate='Czas: %{x} min<br>Moc: %{y:.1f} W'
        )

        fig.add_trace(current_trace_temp, row=1, col=1)
        fig.add_trace(current_trace_P, row=2, col=1)

        previous_trace_temp = go.Scatter(
            x=t, y=temp, mode='lines', line=dict(color='#1074f8', width=2),
            name='T(t) - poprzedni', hovertemplate='Czas: %{x} min<br>Temperatura: %{y:.1f} °C'
        )
        previous_trace_P = go.Scatter(
            x=t[:-1], y=P, mode='lines', line=dict(color='#1074f8', width=2),
            name='P(t) - poprzedni', hovertemplate='Czas: %{x} min<br>Moc: %{y:.1f} W'
        )
        fig.add_trace(go.Scatter(x=t, y=[Temp_zad] * len(t), mode='lines', name='T_zadane', line=dict(dash='dash', color='#afb0b3'), hovertemplate='Czas: %{x} min<br>Temperatura zadana: %{y:.1f} °C'), row=1, col=1)
        
        fig.update_layout(
            height=900,
            plot_bgcolor="#0d1018", paper_bgcolor="#0d1018",
            template="plotly_dark",
            font=dict(
                family="Poppins, sans-serif",
                size=14,
                color="#ffffff"
            )
        )

        fig.update_xaxes(title_text="Czas [min]", color='#e1e2e4', row=1, col=1)
        fig.update_yaxes(title_text="Temperatura [°C]", color='#e1e2e4', row=1, col=1)
        fig.update_xaxes(title_text="Czas [min]", row=2, color='#e1e2e4', col=1)
        fig.update_yaxes(title_text="Wielkość sterująca [W]", color='#e1e2e4', row=2, col=1)


        graph_html = fig.to_html(full_html=False)
    return render_template("index.html", volume=V, kp=kp, temperature=temperature, zad_temperature = zad_temperature, Ti = Ti, graph_html=graph_html)

@app.route("/model")
def model():
    return render_template("model.html")

if __name__ == "__main__":
    app.run(debug=True)