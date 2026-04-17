from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LoreFragment:
    id: str
    text: str
    category: str
    film: str
    year_in_universe: Optional[str] = None
    tags: list[str] = field(default_factory=list)


LORE_FRAGMENTS: list[LoreFragment] = [

    LoreFragment(
        id="char_001",
        text=(
            "Optimus Prime es el líder supremo de los Autobots. "
            "En el universo Bay, llega a la Tierra en 2007 respondiendo al mensaje del AllSpark. "
            "Muere a manos de Megatron en Transformers: Revenge of the Fallen (2009) y es "
            "resucitado por Sam Witwicky usando la Matriz de Liderazgo. "
            "En The Last Knight (2017), es corrompido por Quintessa y se convierte temporalmente "
            "en Nemesis Prime antes de recuperar su identidad. "
            "Nunca pierde su voz ni su capacidad de comunicación verbal en ninguna película."
        ),
        category="PERSONAJE",
        film="SAGA",
        tags=["optimus_prime", "autobot", "lider", "nemesis_prime", "muerte", "resurreccion"],
    ),

    LoreFragment(
        id="char_002",
        text=(
            "Bumblebee es el guardaespaldas y aliado principal de Sam Witwicky. "
            "Perdió su voz en una batalla contra Blitzwing antes de los eventos de TF1 (2007). "
            "Durante TF1-TF3 (2007-2011) se comunica exclusivamente mediante fragmentos de radio "
            "y música. No puede hablar con frases propias en ese período. "
            "Recupera su voz al final del spin-off Bumblebee (2018), ambientado en 1987. "
            "El film Bumblebee (2018) es un prequel, su voz queda destruida "
            "nuevamente antes de TF1 según la cronología interna."
        ),
        category="PERSONAJE",
        film="TF1 / Bumblebee",
        year_in_universe="2007 / 1987",
        tags=["bumblebee", "autobot", "voz", "radio", "sam_witwicky", "guardian"],
    ),

    LoreFragment(
        id="char_003",
        text=(
            "Ironhide es el armero y guerrero veterano de los Autobots. "
            "Sobrevive TF1 y TF2. Muere traicionado por Sentinel Prime al inicio de "
            "Transformers: Dark of the Moon (2011), impactado por su Rifle Oxidante. "
            "No aparece en TF4 ni posteriores. Su muerte es permanente en el canon."
        ),
        category="PERSONAJE",
        film="TF3",
        year_in_universe="2011",
        tags=["ironhide", "autobot", "muerte", "sentinel_prime", "dark_of_the_moon"],
    ),

    LoreFragment(
        id="char_004",
        text=(
            "Ratchet es el médico/cirujano de los Autobots. "
            "Presente en TF1, TF2 y TF3. En Age of Extinction (2014) es asesinado por "
            "los agentes del Gobierno (Cemetery Wind) en los primeros minutos del film, "
            "siendo uno de los Autobots originales eliminados. No aparece vivo después de TF4."
        ),
        category="PERSONAJE",
        film="TF4",
        year_in_universe="2014",
        tags=["ratchet", "autobot", "muerte", "cemetery_wind", "age_of_extinction"],
    ),

    LoreFragment(
        id="char_005",
        text=(
            "Megatron es el líder de los Decepticons y antagonista principal de la saga. "
            "Muere en TF1 (2007) cuando Sam Witwicky le inserta el AllSpark en el pecho. "
            "Resucita en TF2 (2009) mediante una pieza del AllSpark implantada por los Constructicons. "
            "Muere nuevamente al final de TF3 (2011) a manos de Optimus Prime. "
            "Regresa en TF4 (2014) como Galvatron, una reconstrucción robótica de KSI. "
            "Recupera el nombre Megatron en TF5 (2017) y lidera a los Decepticons nuevamente."
        ),
        category="PERSONAJE",
        film="SAGA",
        tags=["megatron", "decepticon", "lider", "galvatron", "muerte", "resurreccion", "allspark"],
    ),

    LoreFragment(
        id="char_006",
        text=(
            "Sentinel Prime fue el predecesor de Optimus Prime como líder Autobot. "
            "Aparece por primera vez en Dark of the Moon (2011) como aliado recuperado. "
            "Revela ser el verdadero villano: traicionó a los Autobots mediante un pacto secreto "
            "con Megatron para reconstruir Cybertron usando trabajo esclavo humano. "
            "Muere al final de TF3 ejecutado por Optimus Prime con su propio rifle. "
            "No existe ni se menciona en ninguna película anterior a TF3."
        ),
        category="PERSONAJE",
        film="TF3",
        year_in_universe="2011",
        tags=["sentinel_prime", "traidor", "decepticon", "aliado", "muerte", "dark_of_the_moon"],
    ),

    LoreFragment(
        id="char_007",
        text=(
            "Starscream es el segundo al mando de los Decepticons y lugarteniente de Megatron. "
            "Presente en TF1, TF2 y TF3. Muere en TF3 (2011) asesinado por Sam Witwicky "
            "con una espina explosiva en el ojo. No aparece después de Dark of the Moon."
        ),
        category="PERSONAJE",
        film="TF3",
        year_in_universe="2011",
        tags=["starscream", "decepticon", "segundo_al_mando", "muerte"],
    ),

    LoreFragment(
        id="char_008",
        text=(
            "Sam Witwicky es el protagonista humano de TF1 (2007), TF2 (2009) y TF3 (2011). "
            "Es bisnieto del Capitán Archibald Witwicky, quien descubrió a Megatron en el Ártico. "
            "No aparece en TF4 (2014), TF5 (2017) ni posteriores. "
            "No existe relación canónica entre Sam y Cade Yeager; son protagonistas de arcos distintos."
        ),
        category="PERSONAJE",
        film="TF1 / TF2 / TF3",
        year_in_universe="2007-2011",
        tags=["sam_witwicky", "humano", "protagonista", "tf1_tf3"],
    ),

    LoreFragment(
        id="char_009",
        text=(
            "Cade Yeager es el protagonista humano desde Age of Extinction (2014) en adelante. "
            "Es un inventor y mecánico de Texas que encuentra a Optimus Prime abandonado. "
            "Aparece en TF4 (2014) y TF5 (2017). "
            "No tiene ningún vínculo establecido con Sam Witwicky en el canon. "
            "No pudo haber interactuado con eventos anteriores a 2014 según la trama."
        ),
        category="PERSONAJE",
        film="TF4 / TF5",
        year_in_universe="2014-2017",
        tags=["cade_yeager", "humano", "protagonista", "tf4_tf5"],
    ),

    LoreFragment(
        id="obj_001",
        text=(
            "El AllSpark es el cubo creador de vida Cybertronian. "
            "TF1 (2007): El cubo es comprimido por Sam y utilizado para destruir a Megatron "
            "insertándolo en su pecho. El cubo queda destruido/fragmentado. "
            "TF2 (2009): Una pieza del AllSpark sobrevive y es usada para resucitar a Megatron. "
            "Después de TF1, el cubo completo no existe; solo fragmentos. "
            "No existe un AllSpark intacto después de los eventos de 2007."
        ),
        category="OBJETO",
        film="TF1 / TF2",
        year_in_universe="2007-2009",
        tags=["allspark", "cubo", "artefacto", "destruido", "fragmento", "megatron"],
    ),

    LoreFragment(
        id="obj_002",
        text=(
            "La Matriz de Liderazgo es un artefacto sagrado Autobot que contiene la sabiduría "
            "de los Primes ancestrales. "
            "TF2 (2009): Sam la busca para resucitar a Optimus Prime. "
            "La Matriz puede derrotar al Caído (The Fallen) y revivir Primes caídos."
        ),
        category="OBJETO",
        film="TF2",
        year_in_universe="2009",
        tags=["matriz_liderazgo", "artefacto", "optimus", "the_fallen", "resurreccion"],
    ),

    LoreFragment(
        id="obj_003",
        text=(
            "El Sector 7 es una agencia gubernamental secreta de EE.UU. que investiga "
            "a los Transformers desde el descubrimiento de Megatron congelado en el Ártico (1897). "
            "Operó hasta TF1 (2007). Fue desmantelado por orden del Secretario de Defensa "
            "Keller al final de TF1. El Sector 7 ya no existe como organización activa "
            "durante los eventos de TF2 en adelante."
        ),
        category="OBJETO",
        film="TF1",
        year_in_universe="1897-2007",
        tags=["sector_7", "gobierno", "agencia", "megatron", "artico", "desmantelado"],
    ),

    LoreFragment(
        id="event_001",
        text=(
            "Transformers (2007): "
            "Los Autobots y Decepticons llegan a la Tierra buscando el AllSpark. "
            "Batalla final en Mission City, California. "
            "Megatron muere a manos de Sam con el AllSpark. "
            "El AllSpark queda destruido. Sector 7 es disuelto."
        ),
        category="EVENTO",
        film="TF1",
        year_in_universe="2007",
        tags=["tf1", "mission_city", "allspark", "megatron_muerte", "sector7"],
    ),

    LoreFragment(
        id="event_002",
        text=(
            "Transformers: Revenge of the Fallen (2009): "
            "Los Decepticons resurgen. The Fallen busca destruir el Sol con un arma antigua. "
            "Optimus Prime muere en el bosque de Shanghai y es resucitado con la Matriz. "
            "Batalla final en Egipto, cerca de las pirámides de Giza. "
            "The Fallen y Megatron son derrotados."
        ),
        category="EVENTO",
        film="TF2",
        year_in_universe="2009",
        tags=["tf2", "revenge_of_fallen", "egipto", "the_fallen", "optimus_muerte", "resurreccion"],
    ),

    LoreFragment(
        id="event_003",
        text=(
            "Transformers: Dark of the Moon (2011): "
            "El Apollo 11 encontró una nave Cybertronian (Ark) en la Luna. "
            "Sentinel Prime traiciona a los Autobots con el Pilar de Espacio para traer Cybertron. "
            "Invasión Decepticon de Chicago. Ironhide y otros Autobots mueren traicionados. "
            "Optimus Prime mata a Sentinel y Megatron al final."
        ),
        category="EVENTO",
        film="TF3",
        year_in_universe="2011",
        tags=["tf3", "chicago", "sentinel_traicion", "luna", "ark", "invasion", "ironhide_muerte"],
    ),

    LoreFragment(
        id="event_004",
        text=(
            "Transformers: Age of Extinction (2014): "
            "5 años después de Chicago, los Autobots son cazados por Cemetery Wind. "
            "Ratchet y otros Autobots originales son eliminados. "
            "KSI reconstruye Transformers artificiales; Galvatron (Megatron reencarnado) emerge. "
            "Los Dinobots (Grimlock, Scorn, Slug, Strafe) aparecen como prisioneros liberados. "
            "Cade Yeager reemplaza a Sam como protagonista humano."
        ),
        category="EVENTO",
        film="TF4",
        year_in_universe="2014",
        tags=["tf4", "cemetery_wind", "dinobots", "galvatron", "ksi", "cade_yeager", "ratchet_muerte"],
    ),

    LoreFragment(
        id="event_005",
        text=(
            "Transformers: The Last Knight (2017): "
            "Optimus Prime viaja a Cybertron y es corrompido por Quintessa, volviéndose Nemesis Prime. "
            "Los Transformers estuvieron en la Tierra desde tiempos de Merlín (siglo V). "
            "Optimus recupera su identidad. Quintessa es aparentemente derrotada."
        ),
        category="EVENTO",
        film="TF5",
        year_in_universe="2017",
        tags=["tf5", "nemesis_prime", "quintessa", "merlin", "caballeros", "cybertron"],
    ),

    LoreFragment(
        id="timeline_001",
        text=(
            "Línea temporal universo Bay: "
            "1897: Capitán Archibald Witwicky descubre a Megatron congelado en el Ártico. "
            "1969: Misión Apollo 11 descubre el Ark en la Luna. "
            "1987: Eventos del spin-off Bumblebee. "
            "2007: Eventos de TF1. "
            "2009: Eventos de TF2. "
            "2011: Eventos de TF3. "
            "2014: Eventos de TF4. "
            "2017: Eventos de TF5."
        ),
        category="TIMELINE",
        film="SAGA",
        tags=["timeline", "cronologia", "fechas", "historia"],
    ),

    LoreFragment(
        id="faction_001",
        text=(
            "Los Autobots son la facción Cybertronian que defiende la vida y la libertad. "
            "Liderados por Optimus Prime. Aliados de los humanos desde TF1. "
            "TF1: Optimus, Bumblebee, Ironhide, Ratchet, Jazz (muere en TF1). "
            "TF2: Se agregan los Twins (Skids y Mudflap), Jolt. "
            "TF3: Se agregan Wheeljack/Que (muere TF3), Dino/Mirage, Roadbuster. "
            "TF4: Autobots restantes + Hound, Drift, Crosshairs, Dinobots. "
            "No existe un Consejo de Cybertron activo en el universo Bay."
        ),
        category="FACCION",
        film="SAGA",
        tags=["autobots", "faccion", "miembros", "jazz_muerte", "consejo_cybertron"],
    ),

    LoreFragment(
        id="faction_002",
        text=(
            "Cybertron, el planeta natal de los Transformers, fue destruido por la guerra. "
            "En TF3, Sentinel Prime intenta traer Cybertron al sistema solar pero el plan fracasa. "
            "No existe un gobierno Cybertronian activo en ningún film Bay. "
            "El concepto del Consejo de Cybertron es exclusivo del universo animado G1."
        ),
        category="FACCION",
        film="SAGA",
        tags=["cybertron", "destruido", "consejo_cybertron", "g1", "canon", "planeta"],
    ),
]


def get_all_fragments():
    return LORE_FRAGMENTS


def get_fragments_by_category(category: str):
    return [f for f in LORE_FRAGMENTS if f.category == category.upper()]


def get_fragments_by_film(film: str):
    return [f for f in LORE_FRAGMENTS if film.upper() in f.film.upper()]


def get_fragment_by_id(fragment_id: str):
    return next((f for f in LORE_FRAGMENTS if f.id == fragment_id), None)


def get_all_texts():
    return [f.text for f in LORE_FRAGMENTS]


if __name__ == "__main__":
    print(f"Total fragmentos: {len(LORE_FRAGMENTS)}")
    for cat in ["PERSONAJE", "EVENTO", "OBJETO", "TIMELINE", "FACCION"]:
        print(f"  {cat}: {len(get_fragments_by_category(cat))}")
