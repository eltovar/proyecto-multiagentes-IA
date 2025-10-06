from datetime import datetime, time
from typing import Dict, Tuple, Optional
from zoneinfo import ZoneInfo


class BusinessHoursConfig:
    """
    Configuración y validación de horarios laborales.

    Clase estática que proporciona métodos para:
    - Verificar si un timestamp está en horario laboral
    - Generar mensajes apropiados fuera de horario
    - Calcular próximo horario hábil
    """

    # Timezone de Colombia
    TIMEZONE = "America/Bogota"

    # Horarios por día de la semana (0=Lunes, 6=Domingo)
    # Formato: (hora_inicio, hora_fin) o None si está cerrado
    HOURS: Dict[int, Optional[Tuple[time, time]]] = {
        0: (time(8, 0), time(18, 0)),   # Lunes
        1: (time(8, 0), time(18, 0)),   # Martes
        2: (time(8, 0), time(18, 0)),   # Miércoles
        3: (time(8, 0), time(18, 0)),   # Jueves
        4: (time(8, 0), time(18, 0)),   # Viernes
        5: (time(8, 0), time(12, 0)),   # Sábado (medio día)
        6: None                          # Domingo (cerrado)
    }

    # Nombres de días en español
    DAY_NAMES = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo"
    }

    @classmethod
    def is_business_hours(cls, dt: Optional[datetime] = None) -> bool:
        """
        Valida si un timestamp está dentro del horario laboral.

        Args:
            dt: Datetime a validar. Si es None, usa datetime.now()

        Returns:
            True si está en horario laboral, False en caso contrario

        Example:
            >>> from datetime import datetime
            >>> # Lunes 10:00 AM
            >>> dt = datetime(2025, 10, 6, 10, 0)
            >>> BusinessHoursConfig.is_business_hours(dt)
            True
            >>> # Domingo 10:00 AM
            >>> dt = datetime(2025, 10, 5, 10, 0)
            >>> BusinessHoursConfig.is_business_hours(dt)
            False
        """
        if dt is None:
            dt = datetime.now(ZoneInfo(cls.TIMEZONE))
        elif dt.tzinfo is None:
            # Si no tiene timezone, asumir Colombia
            dt = dt.replace(tzinfo=ZoneInfo(cls.TIMEZONE))
        else:
            # Convertir a timezone de Colombia
            dt = dt.astimezone(ZoneInfo(cls.TIMEZONE))

        # Obtener día de la semana (0=Lunes, 6=Domingo)
        weekday = dt.weekday()

        # Obtener horario del día
        day_hours = cls.HOURS.get(weekday)

        # Si el día está cerrado
        if day_hours is None:
            return False

        # Extraer hora actual
        current_time = dt.time()

        # Validar si está dentro del rango
        start_time, end_time = day_hours
        return start_time <= current_time <= end_time

    @classmethod
    def get_out_of_hours_message(cls, customer_name: Optional[str] = None) -> str:
        """
        Genera mensaje personalizado para contactos fuera de horario.
            >>> BusinessHoursConfig.get_out_of_hours_message("Carlos")
            'Gracias Carlos por contactarnos.\\n\\nNuestro horario de atención es:...'
        """
        saludo = f"Gracias{' ' + customer_name if customer_name else ''} por contactarnos."

        mensaje = f"""{saludo}

Nuestro horario de atención es:
• Lunes a Viernes: 8:00 AM - 6:00 PM
• Sábados: 8:00 AM - 12:00 PM

Hemos guardado tu consulta y un asesor te contactará en nuestro próximo horario hábil."""

        return mensaje

    @classmethod
    def get_next_business_datetime(cls, from_dt: Optional[datetime] = None) -> datetime:
        """
        Calcula el próximo datetime hábil desde un timestamp dado.

        Args:
            from_dt: Datetime desde el cual calcular. Si es None, usa datetime.now()

        Returns:
            Próximo datetime en horario laboral

        Example:
            >>> # Viernes 7:00 PM (fuera de horario)
            >>> dt = datetime(2025, 10, 3, 19, 0)
            >>> next_dt = BusinessHoursConfig.get_next_business_datetime(dt)
            >>> next_dt
            datetime(2025, 10, 6, 8, 0)  # Lunes 8:00 AM
        """
        if from_dt is None:
            from_dt = datetime.now(ZoneInfo(cls.TIMEZONE))
        elif from_dt.tzinfo is None:
            from_dt = from_dt.replace(tzinfo=ZoneInfo(cls.TIMEZONE))

        # Empezar desde el día siguiente
        check_dt = from_dt.replace(hour=8, minute=0, second=0, microsecond=0)

        # Buscar próximo día hábil (máximo 7 días adelante)
        for _ in range(7):
            check_dt = check_dt.replace(day=check_dt.day + 1)
            weekday = check_dt.weekday()
            day_hours = cls.HOURS.get(weekday)

            if day_hours is not None:
                # Día hábil encontrado, usar hora de inicio
                start_time, _ = day_hours
                return check_dt.replace(
                    hour=start_time.hour,
                    minute=start_time.minute
                )

        # Fallback (no debería llegar aquí)
        return check_dt

    @classmethod
    def get_business_hours_info(cls) -> Dict[str, str]:
        """
        Retorna información estructurada de horarios.

        Returns:
            Dict con horarios formateados por día

        Example:
            >>> info = BusinessHoursConfig.get_business_hours_info()
            >>> info["Lunes"]
            '8:00 AM - 6:00 PM'
        """
        info = {}

        for weekday, day_name in cls.DAY_NAMES.items():
            day_hours = cls.HOURS.get(weekday)

            if day_hours is None:
                info[day_name] = "Cerrado"
            else:
                start_time, end_time = day_hours
                info[day_name] = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"

        return info

    @classmethod
    def format_time_12h(cls, t: time) -> str:
        """
        Formatea time object a formato 12 horas (AM/PM).

        Args:
            t: time object

        Returns:
            String formateado (ej: "8:00 AM")
        """
        return t.strftime("%I:%M %p").lstrip('0')

    @classmethod
    def get_current_status(cls) -> Dict[str, any]:
        """
        Obtiene estado actual del horario laboral.

        Returns:
            Dict con información de estado actual:
            - is_open: bool
            - current_time: str
            - day_name: str
            - message: str

        Example:
            >>> status = BusinessHoursConfig.get_current_status()
            >>> status
            {
                "is_open": True,
                "current_time": "10:30 AM",
                "day_name": "Lunes",
                "message": "Estamos disponibles ahora"
            }
        """
        now = datetime.now(ZoneInfo(cls.TIMEZONE))
        is_open = cls.is_business_hours(now)
        weekday = now.weekday()
        day_name = cls.DAY_NAMES[weekday]
        current_time = cls.format_time_12h(now.time())

        if is_open:
            message = "Estamos disponibles ahora"
        else:
            next_dt = cls.get_next_business_datetime(now)
            next_day = cls.DAY_NAMES[next_dt.weekday()]
            next_time = cls.format_time_12h(next_dt.time())
            message = f"Fuera de horario. Próximo horario: {next_day} {next_time}"

        return {
            "is_open": is_open,
            "current_time": current_time,
            "day_name": day_name,
            "weekday": weekday,
            "message": message
        }


# Ejemplo de uso
if __name__ == "__main__":
    # Test manual
    status = BusinessHoursConfig.get_current_status()
    print("=" * 60)
    print("BUSINESS HOURS STATUS")
    print("=" * 60)
    print(f"Día: {status['day_name']}")
    print(f"Hora actual: {status['current_time']}")
    print(f"Estado: {status['message']}")
    print()

    print("Horarios de atención:")
    for day, hours in BusinessHoursConfig.get_business_hours_info().items():
        print(f"  {day}: {hours}")
