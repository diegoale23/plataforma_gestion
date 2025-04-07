# market_analysis/management/commands/import_jobs.py
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils.dateparse import parse_date
from market_analysis.models import JobOffer, JobSource, Skill

# Importar las clases implementadas
from market_analysis.scraping.infojobs_api_client import InfojobsAPIClient
from market_analysis.scraping.tecnoempleo_scraper import TecnoempleoScraper
from market_analysis.scraping.linkedin_scraper_placeholder import LinkedinScraperPlaceholder
import logging # Usar logging en lugar de solo print

# Configurar un logger simple para el comando
logger = logging.getLogger(__name__)
# Limpiar handlers preexistentes (útil si se ejecuta múltiples veces en un shell interactivo)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
# Añadir un handler básico que imprima a la consola
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO) # Nivel de log (INFO, WARNING, ERROR)


class Command(BaseCommand):
    help = 'Importa ofertas de empleo desde fuentes configuradas (InfoJobs API, Tecnoempleo Scraper, LinkedIn Placeholder)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Fuente específica a importar (InfoJobs, Tecnoempleo, LinkedIn). Si no se especifica, se intentan todas.',
            choices=['InfoJobs', 'Tecnoempleo', 'LinkedIn'],
            default=None
        )
        parser.add_argument('--query', type=str, help='Término de búsqueda para las ofertas.', default='Python')
        parser.add_argument('--location', type=str, help='Ubicación para la búsqueda (ej: Madrid, Asturias).', default='España')
        parser.add_argument('--max-offers', type=int, help='Número máximo de ofertas a intentar obtener por fuente.', default=50)

    def handle(self, *args, **options):
        source_arg = options['source']
        query = options['query']
        location = options['location']
        max_offers = options['max_offers']

        importers = []

        # Decidir qué importadores ejecutar
        if not source_arg or source_arg.lower() == 'infojobs':
            try:
                importers.append(InfojobsAPIClient())
                logger.info(f"Cliente API de InfoJobs inicializado.")
            except ValueError as e:
                 logger.error(f"No se pudo inicializar InfoJobsAPIClient: {e}")
            except Exception as e:
                 logger.error(f"Error inesperado al inicializar InfoJobsAPIClient: {e}")

        if not source_arg or source_arg.lower() == 'tecnoempleo':
            try:
                importers.append(TecnoempleoScraper())
                logger.info("Scraper de Tecnoempleo inicializado.")
            except Exception as e:
                 logger.error(f"Error inesperado al inicializar TecnoempleoScraper: {e}")


        if not source_arg or source_arg.lower() == 'linkedin':
            try:
                importers.append(LinkedinScraperPlaceholder())
                logger.info("Placeholder de LinkedIn inicializado.")
            except Exception as e:
                 logger.error(f"Error inesperado al inicializar LinkedinScraperPlaceholder: {e}")


        if not importers:
            raise CommandError("No se inicializó ningún importador válido. Verifica la configuración o el argumento --source.")

        total_processed_offers = 0
        total_imported_new = 0
        total_skipped_duplicates = 0
        total_failed_imports = 0

        for importer in importers:
            self.stdout.write(self.style.NOTICE(f"\n--- Ejecutando importador: {importer.source_name} ---"))
            logger.info(f"Iniciando obtención de ofertas para {importer.source_name} con query='{query}', location='{location}', max_offers={max_offers}")

            try:
                # Obtener datos formateados del scraper/API client
                offers_data = importer.run(query=query, location=location, max_offers=max_offers)
                if offers_data is None: # run puede devolver None en caso de error grave
                     logger.warning(f"El importador {importer.source_name} devolvió None. Saltando esta fuente.")
                     continue

                num_offers_fetched = len(offers_data)
                total_processed_offers += num_offers_fetched
                logger.info(f"Importador {importer.source_name} obtuvo {num_offers_fetched} ofertas para procesar.")

                # Obtener o crear la JobSource en la BD
                source_obj, created = JobSource.objects.get_or_create(
                    name=importer.source_name,
                    defaults={'url': importer.base_url}
                )
                if created:
                    logger.info(f"Creada nueva JobSource en BD: {source_obj.name}")
                source_obj.last_scraped = timezone.now() # Actualizar fecha de último scrapeo
                source_obj.save()


                imported_count_source = 0
                skipped_count_source = 0
                failed_count_source = 0

                for i, offer_data in enumerate(offers_data):
                    logger.debug(f"Procesando oferta {i+1}/{num_offers_fetched} de {importer.source_name}: {offer_data.get('url')}")

                    # Validar datos mínimos (URL es crucial)
                    offer_url = offer_data.get('url')
                    offer_title = offer_data.get('title')
                    if not offer_url or not offer_title:
                        logger.warning(f"Oferta de {importer.source_name} descartada - falta URL o título: {offer_data}")
                        failed_count_source += 1
                        continue

                    try:
                        # Intentar crear o actualizar (get_or_create basado en URL)
                        job, created = JobOffer.objects.update_or_create(
                            url=offer_url, # Clave única para buscar/crear
                            defaults={ # Campos a actualizar o establecer si se crea
                                'title': offer_title,
                                'company': offer_data.get('company'),
                                'location': offer_data.get('location'),
                                'description': offer_data.get('description'),
                                'salary_range': offer_data.get('salary_range'),
                                'publication_date': parse_date(offer_data.get('publication_date')) if offer_data.get('publication_date') else None,
                                'source': source_obj,
                                'applicants_count': offer_data.get('applicants_count'),
                                'raw_data': offer_data.get('raw_data'),
                                'is_active': True, # Marcar como activa al importar/actualizar
                                # updated_at se actualiza automáticamente
                            }
                        )

                        if created:
                            logger.info(f"IMPORTADA NUEVA: '{job.title}' @ '{job.company}' ({importer.source_name})")
                            imported_count_source += 1
                        else:
                            # logger.info(f"ACTUALIZADA: '{job.title}' ({importer.source_name})") # Log opcional para actualizaciones
                            # Podríamos contar actualizaciones si quisiéramos
                            skipped_count_source += 1 # Contamos como "saltado" si ya existía

                        # Procesar y añadir/actualizar habilidades
                        current_skills_in_offer = set(job.required_skills.all())
                        found_skill_objs = set()
                        skills_list = offer_data.get('required_skills', [])
                        if isinstance(skills_list, list):
                            for skill_name in skills_list:
                                clean_skill_name = skill_name.strip().lower()
                                if clean_skill_name:
                                    # Usar get_or_create para la habilidad en sí
                                    skill_obj, skill_created = Skill.objects.get_or_create(
                                        name__iexact=clean_skill_name, # Búsqueda case-insensitive
                                        defaults={'name': clean_skill_name.capitalize()} # Guardar capitalizado
                                    )
                                    if skill_created:
                                        logger.debug(f"  - Creada nueva Skill: {skill_obj.name}")
                                    found_skill_objs.add(skill_obj)

                            # Añadir habilidades nuevas a la oferta
                            skills_to_add = found_skill_objs - current_skills_in_offer
                            if skills_to_add:
                                job.required_skills.add(*skills_to_add)
                                logger.debug(f"  - Añadidas skills a oferta '{job.title}': {[s.name for s in skills_to_add]}")

                            # Opcional: Eliminar habilidades que ya no están en la fuente (más complejo, requiere cuidado)
                            # skills_to_remove = current_skills_in_offer - found_skill_objs
                            # if skills_to_remove:
                            #    job.required_skills.remove(*skills_to_remove)
                            #    logger.debug(f"  - Eliminadas skills de oferta '{job.title}': {[s.name for s in skills_to_remove]}")

                    except IntegrityError as e:
                        logger.error(f"Error de Integridad (posible duplicado no detectado?) para {offer_url}: {e}")
                        failed_count_source += 1
                    except Exception as e:
                        logger.exception(f"Error inesperado al guardar la oferta {offer_url} de {importer.source_name}: {e}") # logger.exception incluye traceback
                        failed_count_source += 1

                # Resumen por fuente
                self.stdout.write(f"  Resumen {importer.source_name}: "
                                  f"Nuevas: {imported_count_source}, "
                                  f"Existentes/Actualizadas: {skipped_count_source}, "
                                  f"Fallidas: {failed_count_source}")
                total_imported_new += imported_count_source
                total_skipped_duplicates += skipped_count_source
                total_failed_imports += failed_count_source

            except Exception as e:
                logger.exception(f"FALLO GRAVE en el importador {importer.source_name}: {e}")
                self.stdout.write(self.style.ERROR(f"El importador {importer.source_name} falló completamente."))


        # Resumen final
        self.stdout.write(self.style.SUCCESS(f"\n--- Importación Finalizada ---"))
        self.stdout.write(f"Total ofertas procesadas de fuentes: {total_processed_offers}")
        self.stdout.write(f"Total NUEVAS ofertas importadas: {total_imported_new}")
        self.stdout.write(f"Total ofertas existentes/actualizadas: {total_skipped_duplicates}")
        self.stdout.write(f"Total ofertas fallidas al guardar: {total_failed_imports}")


# Necesitas importar timezone para actualizar JobSource.last_scraped
from django.utils import timezone