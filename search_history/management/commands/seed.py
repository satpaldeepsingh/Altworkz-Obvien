from django.core.management.base import BaseCommand
from search_history.models import SearchFilter
from search_history.models import SearchFilterValue
# python manage.py seed --mode=refresh

""" Clear all data and creates addresses """
MODE_REFRESH = 'refresh'

""" Clear all data and do not create any object """
MODE_CLEAR = 'clear'


class Command(BaseCommand):
    help = "seed database for testing and development."

    def add_arguments(self, parser):
        parser.add_argument('--mode', type=str, help="Mode")

    def handle(self, *args, **options):
        self.stdout.write('seeding data...')
        run_seed(self, options['mode'])
        self.stdout.write('done.')


def clear_data():
    """Deletes all the table data"""

    SearchFilter.objects.all().delete()
    SearchFilterValue.objects.all().delete()


def insert_filters():
    """Insert Filters List"""

    filter_names = ["location_country", "location_city", "location_area",
                    "relationship_degree_of_relationship", "relationship_warmth_of_relationship",
                    "comapny_type", "comapny_number_of_employees", "comapny_industry", "comapny_sub_sector",
                    "education_school_college", "education_degree",
                    "industory_sector",
                    "function",
                    "job_title",
                    "seniority_level_years_in_current_position", "seniority_level_years_at_current_company",
                    "member_of_platform",
                    ]
    for filter_name in filter_names:

        filters = SearchFilter(
            filter_name=filter_name

        )
        filters.save()

    return filter_names


def insert_filters_values():
    """Insert Filters Values"""

    filter_values = ["VI", "SWI",
                     "DM", "NI"]
    for filter_value in filter_values:

        filters = SearchFilterValue(
            filter_value=filter_value

        )
        filters.save()

    return filter_values


def run_seed(self, mode):
    """ Seed database based on mode

    :param mode: refresh / clear 
    :return:
    """
    # Clear data from tables
    clear_data()
    if mode == MODE_CLEAR:
        return

    insert_filters()
    insert_filters_values()
