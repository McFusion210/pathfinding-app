 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/app.py b/app.py
index 21a5ab7ada6f1bf34dd3cca67e8c0969896fa872..b7e412bb664d36af374eb837bbd5da2fbfaee4db 100644
--- a/app.py
+++ b/app.py
@@ -1052,57 +1052,65 @@ else:
                          or "<span class='placeholder'>No additional details</span>")
 
             st.markdown(f"<div class='meta-info'>{meta_html}</div>", unsafe_allow_html=True)
 
             # Actions row: Website · Email · Call · ☆/★ Favourite
             st.markdown("<div class='actions-row'>", unsafe_allow_html=True)
 
             cols = st.columns(4)
             call_clicked = False
             fav_clicked = False
 
             # Website
             with cols[0]:
                 if website:
                     url = website if website.startswith(("http://","https://")) else f"https://{website}"
                     st.markdown(f"[Website]({url})", unsafe_allow_html=True)
 
             # Email
             with cols[1]:
                 if email:
                     st.markdown(f"[Email](mailto:{email})", unsafe_allow_html=True)
 
             # Call (inline control toggles numbers)
             with cols[2]:
                 if phone_display_multi:
-                    call_clicked = st.button("Call", key=f"call_{key}")
+                    call_clicked = st.button(
+                        "Call",
+                        key=f"call_{key}",
+                        type="secondary",
+                    )
 
             # Favourite (inline control)
             with cols[3]:
                 fav_on = key in st.session_state.favorites
                 fav_label = "★ Favourite" if fav_on else "☆ Favourite"
-                fav_clicked = st.button(fav_label, key=f"fav_{key}")
+                fav_clicked = st.button(
+                    fav_label,
+                    key=f"fav_{key}",
+                    type="secondary",
+                )
 
             st.markdown("</div>", unsafe_allow_html=True)  # close actions-row
 
             # Toggle phone number display when Call is clicked
             if phone_display_multi:
                 call_state_key = f"show_call_{key}"
                 if call_clicked:
                     st.session_state[call_state_key] = not st.session_state.get(call_state_key, False)
                 if st.session_state.get(call_state_key, False):
                     st.markdown(
                         f"<small><strong>Call:</strong> {phone_display_multi}</small>",
                         unsafe_allow_html=True,
                     )
 
             # Toggle favourites
             if fav_clicked:
                 if fav_on:
                     st.session_state.favorites.remove(key)
                 else:
                     st.session_state.favorites.add(key)
                 st.rerun()
 
             if len(desc_full) > 240:
                 with st.expander("More details"):
                     st.markdown(f"**Full description:** {desc_full}")
 
EOF
)
