"""Gráficas Plotly de la app, con la paleta de tema.py."""

import plotly.graph_objects as go

from megamarket_app.tema import CRITERIO_AG, PALETA, SEMANTICOS

FUENTE = "Montserrat, sans-serif"


def _estilo(fig, titulo_x, titulo_y, alto=380):
    fig.update_layout(
        height=alto,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(family=FUENTE, color=PALETA["texto"], size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PALETA["blanco"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(font_family=FUENTE),
    )
    fig.update_xaxes(title=titulo_x, gridcolor=PALETA["borde"], zeroline=False)
    fig.update_yaxes(title=titulo_y, gridcolor=PALETA["borde"], zeroline=False)
    return fig


def burbujas_candidatos(candidatos, elegidos=()):
    """Costo vs. utilidad de cada candidato; tamaño = espacio de bodega."""
    nombres = list(candidatos)
    colores = [PALETA["azul_rey"] if n in elegidos else PALETA["azul_medio"] for n in nombres]
    fig = go.Figure(go.Scatter(
        x=[candidatos[n]["costo_lanzamiento"] / 1e6 for n in nombres],
        y=[candidatos[n]["utilidad_esperada_anual"] / 1e6 for n in nombres],
        mode="markers+text",
        text=[n.replace(" Riovalle", "") for n in nombres],
        textposition="top center",
        marker=dict(
            size=[candidatos[n]["espacio_bodega"] for n in nombres],
            sizemode="area", sizeref=2.0 * max(c["espacio_bodega"] for c in candidatos.values()) / 45 ** 2,
            sizemin=6, color=colores, opacity=0.85, line=dict(color="white", width=1.5),
        ),
        customdata=[[candidatos[n]["espacio_bodega"]] for n in nombres],
        hovertemplate="<b>%{text}</b><br>Costo: $%{x:.1f} M<br>Utilidad: $%{y:.1f} M<br>Espacio: %{customdata[0]} posiciones<extra></extra>",
    ))
    return _estilo(fig, "Costo de lanzamiento (millones COP)", "Utilidad esperada anual (millones COP)", 420)


def evolucion_ag(historial, columna_mejor, columna_promedio, color_mejor, nombre_mejor, nombre_promedio):
    """Mejor y promedio de la población por generación (millones COP)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historial["Generación"], y=historial[columna_mejor] / 1e6, name=nombre_mejor,
        mode="lines+markers", line=dict(color=color_mejor, width=3),
        hovertemplate="Generación %{x}<br>$%{y:.1f} M<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=historial["Generación"], y=historial[columna_promedio] / 1e6, name=nombre_promedio,
        mode="lines+markers", line=dict(color=SEMANTICOS["advertencia"], width=2, dash="dot"),
        hovertemplate="Generación %{x}<br>$%{y:.1f} M<extra></extra>",
    ))
    return _estilo(fig, "Generación", "Millones COP")


def diversidad(historial):
    """Cuántos portafolios distintos hay en cada generación."""
    fig = go.Figure(go.Bar(
        x=historial["Generación"], y=historial["Diversidad"], marker_color=PALETA["azul_medio"],
        hovertemplate="Generación %{x}<br>%{y} portafolios distintos<extra></extra>",
    ))
    return _estilo(fig, "Generación", "Portafolios distintos")


def ataques_minimax(ataques, utilidad_esperada):
    """Nivel MIN del árbol: lo que queda si el rival ataca cada producto."""
    productos = [p for p, _ in ataques]
    quedan = [v / 1e6 for _, v in ataques]
    colores = [CRITERIO_AG["peor_caso"] if i == 0 else PALETA["azul_medio"] for i in range(len(ataques))]
    fig = go.Figure(go.Bar(
        x=quedan, y=productos, orientation="h", marker_color=colores,
        text=[f"${v:.1f} M" for v in quedan], textposition="outside",
        hovertemplate="Si el rival ataca %{y}: quedan $%{x:.1f} M<extra></extra>",
    ))
    fig.add_vline(x=utilidad_esperada / 1e6, line_dash="dot", line_color=PALETA["gris"],
                  annotation_text="sin rival", annotation_position="top")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(range=[0, utilidad_esperada / 1e6 * 1.15])
    return _estilo(fig, "Utilidad que queda (millones COP)", "", 80 + 50 * len(ataques))


def costo_de_protegerse(puntos, destacados):
    """Utilidad esperada vs. peor caso de todos los portafolios válidos.

    puntos: lista de (esperada, peor_caso, etiqueta).
    destacados: lista de (esperada, peor_caso, nombre, color).
    """
    fig = go.Figure(go.Scatter(
        x=[p[0] / 1e6 for p in puntos], y=[p[1] / 1e6 for p in puntos], mode="markers",
        name="Otros portafolios válidos", text=[p[2] for p in puntos],
        marker=dict(size=8, color="#B8C0CC", opacity=0.8),
        hovertemplate="%{text}<br>Esperada $%{x:.1f} M · Peor caso $%{y:.1f} M<extra></extra>",
    ))
    for esperada, peor, nombre, color in destacados:
        fig.add_trace(go.Scatter(
            x=[esperada / 1e6], y=[peor / 1e6], mode="markers", name=nombre,
            marker=dict(size=16, color=color, line=dict(color="white", width=2)),
            hovertemplate=f"{nombre}<br>Esperada $%{{x:.1f}} M · Peor caso $%{{y:.1f}} M<extra></extra>",
        ))
    return _estilo(fig, "Utilidad esperada (millones COP)", "Utilidad en el peor caso (millones COP)", 440)
