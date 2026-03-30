import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title='Filtro Smash Pro', layout='wide')

st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
.kpi {background: #111827; color: white; padding: 18px; border-radius: 16px;}
</style>
""", unsafe_allow_html=True)

st.title('🍔 Filtro Smash Pro')
st.caption('Sube tu Excel, busca productos y descarga resultados con un clic')

uploaded = st.file_uploader('Sube tu archivo Excel', type=['xlsx'])

if uploaded:
    try:
        xls = pd.ExcelFile(uploaded)
        sheet = 'Hoja1' if 'Hoja1' in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(uploaded, sheet_name=sheet, header=1)
        df.columns = [str(c).strip() for c in df.columns]

        if 'Nombre del producto' not in df.columns:
            st.error('No se encontró la columna Nombre del producto.')
            st.stop()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            q = st.text_input('Buscador', value='smash', placeholder='Escribe un producto')
        with c2:
            min_qty = st.number_input('Cantidad mínima', min_value=0.0, value=0.0, step=1.0)
        with c3:
            only_smash = st.toggle('Solo smash', value=True)
        with c4:
            search_btn = st.button('Aplicar filtro', type='primary')

        query = q.strip()
        if only_smash and 'smash' not in query.lower():
            query = (query + ' smash').strip()
        if not query:
            query = 'smash' if only_smash else ''

        if not search_btn:
            st.info('Configura los filtros y presiona **Aplicar filtro**.')
            st.stop()

        mask = df['Nombre del producto'].astype(str).str.contains(query, case=False, na=False)
        data = df.loc[mask].copy()

        if 'Cantidad vendida' in data.columns:
            data['Cantidad vendida'] = pd.to_numeric(data['Cantidad vendida'], errors='coerce').fillna(0)
            data = data[data['Cantidad vendida'] >= min_qty]
        if 'Precio total' in data.columns:
            data['Precio total'] = pd.to_numeric(data['Precio total'], errors='coerce').fillna(0)

        total_lines = len(data)
        total_qty = float(data['Cantidad vendida'].sum()) if 'Cantidad vendida' in data.columns else 0
        total_sales = float(data['Precio total'].sum()) if 'Precio total' in data.columns else 0
        avg_ticket = total_sales / total_lines if total_lines else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="kpi"><h4>Líneas</h4><h2>{total_lines}</h2></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi"><h4>Unidades</h4><h2>{total_qty:.0f}</h2></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi"><h4>Venta total</h4><h2>S/ {total_sales:,.2f}</h2></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi"><h4>Ticket prom.</h4><h2>S/ {avg_ticket:,.2f}</h2></div>', unsafe_allow_html=True)

        st.markdown('### Resultados')
        view_cols = [c for c in ['Número de venta', 'Fecha y hora de la venta', 'Nombre del producto', 'Categoría del producto', 'Cantidad vendida', 'Precio total'] if c in data.columns]
        st.dataframe(data[view_cols] if view_cols else data, use_container_width=True, height=420)

        st.markdown('### Resumen por producto')
        agg = pd.DataFrame()
        if 'Cantidad vendida' in data.columns and 'Precio total' in data.columns and not data.empty:
            agg = data.groupby('Nombre del producto', as_index=False).agg(
                Cantidad_vendida=('Cantidad vendida', 'sum'),
                Precio_total=('Precio total', 'sum')
            ).sort_values(['Cantidad_vendida', 'Precio_total'], ascending=False)
            st.dataframe(agg, use_container_width=True, height=320)

        col_a, col_b = st.columns(2)
        with col_a:
            if not data.empty:
                top = data['Nombre del producto'].value_counts().head(10)
                st.bar_chart(top)
        with col_b:
            if 'Cantidad vendida' in data.columns and not data.empty:
                st.bar_chart(data.groupby('Categoría del producto', dropna=False)['Cantidad vendida'].sum().sort_values(ascending=False).head(10))

        out = BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name='Filtrado')
            if not agg.empty:
                agg.to_excel(writer, index=False, sheet_name='Resumen')
        st.download_button('⬇️ Descargar Excel filtrado', data=out.getvalue(), file_name='smash_pro_filtrado.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        csv_bytes = data.to_csv(index=False).encode('utf-8-sig')
        st.download_button('⬇️ Descargar CSV', data=csv_bytes, file_name='smash_pro_filtrado.csv', mime='text/csv')

        if st.button('Limpiar filtros'):
            st.rerun()

    except Exception as e:
        st.error(f'Error al procesar el archivo: {e}')