var search_filters_array = null;
var search_del_obj = {};
var bulleteImg = null;
var search_obj = {};
var field_placeholders = {};
var contact_id_list = [];
var first_search_after_pageload = true;
var user_isa = false;

var remote_response_graph = [];
var remote_sec_deg_connection_details = [];
var common_elements_among_search_results = {'edu': {'__max__': {'edu': '', 'count': 0}}, 'job': {'__max__': {'org': '', 'count': 0}}};

var file_tags_suggestions_list = [];
let file_tags_checkbox_list = '';

var current_page = 1;
var prev_search = '';

function sortFilterList (first, second) {
  if (first.toLowerCase() < second.toLowerCase()) {
    return -1;
  }
  if (first.toLowerCase() > second.toLowerCase()) {
    return 1;
  }
  return 0;
}

function show_loader () {

    $('.aw_wrapper').preloader({
        text: 'Please Wait...',
        percent: '',
        duration: '',
        zIndex: '',
        setRelative: false
    });

}

function viewSaveSearch(data) {
    search_view_obj = {};

    var seachKey = data.getAttribute("data-search");
    var seachFilters = data.getAttribute("data-filters");
    var seachFilterWeights = data.getAttribute("data-filter-weights");
    search_view_obj['search_str'] = seachKey;

    if (seachFilters != "null") {
        search_view_obj['filters'] = JSON.parse(seachFilters);
        search_obj['filters'] = search_view_obj['filters'];
        var filters = JSON.parse(seachFilters);
        var num_of_filters = Object.keys(filters).length;
		

        for (i = 0; i < Object.keys(filters).length; i++) {
            
			var filter_name = Object.keys(filters)[i];
            var filter_value = filters[filter_name];

            search_view_obj['filters'][filter_name] = filter_value;

            field_placeholders[filter_name] = $(`input[name="${filter_name}"]`).attr('placeholder');

        }

    }

    if (seachFilterWeights != "null") {
        search_view_obj['filter_weights'] = JSON.parse(seachFilterWeights);
        search_view_obj['view_saved_search'] = true;
    }


    document.getElementById("search-text").value = seachKey;
    execute_search(search_view_obj);
    let filters_li = '';


    for (let filter_key in search_view_obj['filters']) {

        let placeholder = $(`input[name="${filter_key}"]`).attr('placeholder');
        //            let placeholder = field_placeholders[filter_key];

        filters_li += `<li filter-name="${filter_key}"><span>${placeholder} <b>${search_view_obj['filters'][filter_key]}</b> <i class="fas fa-times"></i></span></li>`;

    }
    $('#applied-filters-ul').html(filters_li);

    for (let filter_key in search_view_obj['filters']) {

        //            let placeholder = field_placeholders[filter_key];
        if (filter_key == 'job_title') {
            document.getElementById("job_title").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'degree') {
            document.getElementById("degree").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'school_name') {
            document.getElementById("school_name").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'organization_name') {
            document.getElementById("organization_name").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'industry') {
            document.getElementById("industry").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'sub_industry') {
            document.getElementById("sub_industry").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'number_of_employees') {
            document.getElementById("number_of_employees").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'country') {
            document.getElementById("country").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'city') {
            document.getElementById("city").value = search_view_obj['filters'][filter_key];
        }
        if (filter_key == 'area') {
            document.getElementById("area").value = search_view_obj['filters'][filter_key];
        }

    }
}

(function ($) {
    "use strict";

    //$('#modalMutualConnections').modal('show');

    var swiper_instance = null;

    $('#search-text').on('focus', function () {
        $('.search-validation-msg').hide();
        $('.backend-error-msg').hide();
        $(this).css({ 'border': '1px solid #007bff' });
    });

    $(".aw_filters_list").on("click", ".aw_filter_link", function (e) {

        var elem = $(this);
        var siblings = elem.siblings();
        var parent = elem.parent();
        var parentSiblings = parent.siblings();

        parentSiblings.children('.aw_filter_fields').slideUp('slow')
        siblings.slideToggle("slow");

        e.preventDefault();
    });

    var unqiue_photo_list = []; // temp arrangement for duplicate removals
	
	function perform_new_search () {
		
		current_page = 1;
		search(1);
		
	}

    function search(page_num=1) {

        var search_str = $('#search-text').val();

        if (search_str == '') {
            
			$('.search-validation-msg').show();
            $('#search-text').css({'border': '1px solid #d05353'});
            
			return false;
        
		}

        $('.aw_wrapper').preloader({
            text: 'Please Wait...',
            percent: '',
            duration: '',
            zIndex: '',
            setRelative: false
        });

        search_obj['search_str'] = search_str;
        search_obj['first_search_after_pageload'] = first_search_after_pageload;
        search_obj['page_num'] = page_num;
		console.log('selected page ', page_num);

        if ('filters' in search_obj && search_obj['filters'].length == 0) {
            
			delete search_obj['filters'];
        
		}

        search_filters_array = search_obj;
        execute_search(search_obj);

    }

    function execute_search(search_obj) {

        let search_feedback = get_search_feedback();

        show_loader();
		try{
		$.ajax({
			url: '/get-filter-suggestions',
			dataType: 'json',
			data: search_obj,
			success: function (data) {
				
				let job_profile_org_suggest_list = [];
				let job_profile_tilte_suggest_list = [];
				let edu_profile_school_suggest_list = [];
				let edu_profile_degree_suggest_list = [];
				data.forEach(job_edu_profile => {
					if ('job_profile' in job_edu_profile) {
						if (job_edu_profile['job_profile'][0]['organization_'] !== null) {
							job_profile_org_suggest_list.push(job_edu_profile['job_profile'][0]['organization_'])
						}
						if (job_edu_profile['job_profile'][0]['organization_title_'] !== null) {
							job_profile_tilte_suggest_list.push(job_edu_profile['job_profile'][0]['organization_title_']);									
						}									
					}
					if ('edu_profile' in job_edu_profile) {
						if (job_edu_profile['edu_profile'][0]['school_'] !== null) {
							edu_profile_school_suggest_list.push(job_edu_profile['edu_profile'][0]['school_'])
						}	
						if (job_edu_profile['edu_profile'][0]['degree_'] !== null) {
							edu_profile_degree_suggest_list.push(job_edu_profile['edu_profile'][0]['degree_'])
						}						
					}
				});
            }
            catch(e) {
                console.error(e);
            }
				$('#organization_name').easyAutocomplete({
					data: job_profile_org_suggest_list.filter((value, index, self) => self.indexOf(value) === index).sort(sortFilterList),
					list: {
						maxNumberOfElements:job_profile_org_suggest_list.length,
						hideOnEmptyPhrase: false,
						match: {                    
							enabled: true
						},
						onClickEvent: function () {
							change_field_value_on_selection('organization_name');
						},
						onSelectItemEvent: function () {
							change_field_value_on_selection('organization_name', 'onSelectItemEvent');
						},
						onChooseEvent: function () {
							change_field_value_on_selection('organization_name');
						}
					},
					adjustWidth: false,
				});

				$('#school_name').easyAutocomplete({
					data: edu_profile_school_suggest_list.filter((value, index, self) => self.indexOf(value) === index).sort(sortFilterList),
					list: {
						maxNumberOfElements:edu_profile_school_suggest_list.length,
						hideOnEmptyPhrase: false,
						match: {
							enabled: true
						},
						onClickEvent: function () {
							change_field_value_on_selection('school_name');
						},
						onSelectItemEvent: function () {
							change_field_value_on_selection('school_name', 'onSelectItemEvent');
						},
						onChooseEvent: function () {
							change_field_value_on_selection('school_name');
						}
					},
					adjustWidth: false,
				});
				
				console.log('edu degree ', edu_profile_degree_suggest_list);

				$('#degree').easyAutocomplete({
					data: edu_profile_degree_suggest_list.filter((value, index, self) => self.indexOf(value) === index).sort(sortFilterList),
					list: {
						maxNumberOfElements:edu_profile_degree_suggest_list.length,
						hideOnEmptyPhrase: false,
						match: {
							enabled: true
						},
						onClickEvent: function () {
							change_field_value_on_selection('degree');
						},
						onSelectItemEvent: function () {
							change_field_value_on_selection('degree', 'onSelectItemEvent');
						},
						onChooseEvent: function () {
							change_field_value_on_selection('school_name');
						}
					},
					adjustWidth: false,
				});

				
				$('#job_title').easyAutocomplete({
					data: job_profile_tilte_suggest_list.filter((value, index, self) => self.indexOf(value) === index).sort(sortFilterList),
					list: {
						maxNumberOfElements:job_profile_tilte_suggest_list.length,
						hideOnEmptyPhrase: false,
						match: {
							enabled: true
						},
						onClickEvent: function () {
							change_field_value_on_selection('job_title');
						},
						onSelectItemEvent: function () {
							change_field_value_on_selection('job_title', 'onSelectItemEvent');
						},
						onChooseEvent: function () {
							change_field_value_on_selection('job_title');
						}
					},
					adjustWidth: false,
				});				
				
			}
		});			
		
        var html;
        $.ajax({
            url: '/elastic-search',
            dataType: 'json',
            data: search_obj,
            success: function (data) {

                user_isa = data.staff;
                $('.aw_section_recommendation').hide();
                $('.aw_recent_searches').hide();
                $('.aw_section_recent_browse').hide();
                $('.aw_section_saved_searches').hide();
                //$('.pagination').hide();
                $('.swiper-wrapper').html('');
                $('#searchResults').html('');
                $('.google_result_list').html('');
                $('.not-found-results').html('');
                if (swiper_instance !== null) {
                    swiper_instance.destroy();
                    $('#resultsCarousel').hide();
                }
                $('.aw_google_result').hide();

                var firsDegreeContacts = data.first_degree;
                var secondDegreeContacts = data.second_degree;
                var thirdDegreeContacts = data.third_degree;
				
				var total_results = data.total_results;
        
															
                    $('#resultsCarousel').show();
                    bulleteImg = [];
                    unqiue_photo_list = [];
                    let result_count = 0;
                    let job_titles_list = [];
                    let companies_list = [];
                    let schools_list = [];
                    let industries_list = [];
                    let platforms_list = [];
					let org_cities_list = [];
					let org_countries_list = [];
//                    let org_cities_list = ['Lahore', 'Los Angeles'];
//                    let org_countries_list = ['Pakistan', 'United States'];


                    $.each(data.results, function () {
                        console.log(this);
                        contact_id_list.push(this['contact_id']);
                        if (this != false) {
                            if (this['photo'] === undefined || this['photo'] == '' || this['photo'] === null) {
                                this['photo'] = '/static/img/avatar.png';
                            }
                            //if (this['photo'] != '' && this['photo'] !== null && unqiue_photo_list.indexOf(this['photo']) === -1) {
                                bulleteImg.push(this['photo']);
                                $('#searchResults').append(result_card(this, firsDegreeContacts, secondDegreeContacts, thirdDegreeContacts, search_feedback));
                                swiper_slider(this, firsDegreeContacts, secondDegreeContacts, thirdDegreeContacts, data);
                                if (this['photo'] != '/static/img/avatar.png') {
                                    unqiue_photo_list.push(this['photo']);
                                }
                                result_count++;
                            //}
							
                        }
						
						$('#light-pagination').pagination({
							items: total_results,
							itemsOnPage: 20,
							currentPage: current_page,
							cssStyle: 'light-theme',
							onPageClick: function (page_num, event) {
								current_page = page_num;
								search(page_num);
							}
						});							
							
                    });
										
                

					/*
					
					var filters_id_list = {
						'job_title' : job_titles_list, 
						'industry': industries_list, 
						'organization_name': companies_list, 
						'school_name': schools_list
					};					
					
					for (let filter_id_list_item in filters_id_list) {
						
						$(`#${filter_id_list_item}`).easyAutocomplete({
							data: job_titles_list.filter((value, index, self) => self.indexOf(value) === index),
							list: {
								maxNumberOfElements:job_titles_list.length,
								hideOnEmptyPhrase: false,
								match: {
									enabled: true
								},
								onClickEvent: function () {
									change_field_value_on_selection(`${filter_id_list_item}`);
								},
								onSelectItemEvent: function () {
									change_field_value_on_selection(`${filter_id_list_item}`, 'onSelectItemEvent');
								},
								onChooseEvent: function () {
									change_field_value_on_selection(`${filter_id_list_item}`);
								}
							},
							adjustWidth: false,
						});						
						
						
						console.log('initializing list filter item ', filter_id_list_item);
						
					}
					*/



                    $('#industry').easyAutocomplete({
                        data: industries_list.filter((value, index, self) => self.indexOf(value) === index),
                        list: {
							maxNumberOfElements:industries_list.length,
							hideOnEmptyPhrase: false,
                            match: {
                                enabled: true
                            },
							onClickEvent: function () {
								change_field_value_on_selection('industry');
							},
							onSelectItemEvent: function () {
								change_field_value_on_selection('industry', 'onSelectItemEvent');
							},
							onChooseEvent: function () {
								change_field_value_on_selection('industry');
							}
                        },
                        adjustWidth: false,
                    });
					// organization name suggestion list
					/*
                    $('#organization_name').easyAutocomplete({
                        data: companies_list.filter((value, index, self) => self.indexOf(value) === index),
                        list: {
							maxNumberOfElements:companies_list.length,
							hideOnEmptyPhrase: false,
                            match: {
                                enabled: true
                            },
							onClickEvent: function () {
								change_field_value_on_selection('organization_name');
							},
							onSelectItemEvent: function () {
								change_field_value_on_selection('organization_name', 'onSelectItemEvent');
							},
							onChooseEvent: function () {
								change_field_value_on_selection('organization_name');
							}
                        },
                        adjustWidth: false,
                    });
					// school name suggestion list
                    $('#school_name').easyAutocomplete({
                        data: schools_list.filter((value, index, self) => self.indexOf(value) === index),
                        list: {
							maxNumberOfElements:schools_list.length,
							hideOnEmptyPhrase: false,
                            match: {
                                enabled: true
                            },
							onClickEvent: function () {
								change_field_value_on_selection('school_name');
							},
							onSelectItemEvent: function () {
								change_field_value_on_selection('school_name', 'onSelectItemEvent');
							},
							onChooseEvent: function () {
								change_field_value_on_selection('school_name');
							}
                        },
                        adjustWidth: false,
                    });
					*/	

                    let file_tag_list = '';
                    let file_tags_suggestions_count = data.file_tags_suggestions.length;

                    if (file_tags_suggestions_count > 0) {

                        let all_filetags_checked = 'checked';
                        let selected_filetags_length = 0;

                        if (file_tags_checkbox_list !== '') {
                            if (typeof file_tags_checkbox_list == 'object' && file_tags_checkbox_list.length < data.file_tags_suggestions.length) {
                                selected_filetags_length = file_tags_checkbox_list.length;
                                all_filetags_checked = '';
                            }
                        }

                        file_tag_list = `<div class="col col-md-12"><input type="checkbox" id="all-file-tags" value="all" class="file-tags-suggestions" ${all_filetags_checked} /> <label>All</label></div>`;

                        for (let ftl = 0; ftl < file_tags_suggestions_count; ftl++) {

                            file_tags_suggestions_list.push(data.file_tags_suggestions[ftl]);

                            let ind_filetag_checked = 'checked';

                            if (file_tags_checkbox_list !== '') {

                                if (typeof file_tags_checkbox_list == 'object') {

                                    if (file_tags_checkbox_list.indexOf(data.file_tags_suggestions[ftl]) == -1) {

                                        ind_filetag_checked = '';
										
                                    }

                                }

                            }

                            file_tag_list += `<div class="col col-md-12"><input type="checkbox" value="${data.file_tags_suggestions[ftl]}" class="file-tags-suggestions" ${ind_filetag_checked} /> <label>${data.file_tags_suggestions[ftl]}</label></div>`;

                        }

                        file_tag_list += `<button class="btn btn-primary" id="apply-file-tag-filter">Apply File Tag Filter</button>`;

                    }

                    $('#file-tag-checkbox-list').html(file_tag_list);

                    $('#file_tag').easyAutocomplete({
                        data: data.file_tags_suggestions,
                        list: {
							maxNumberOfElements:data.file_tags_suggestions.length,
							hideOnEmptyPhrase: false,
                            match: {
                                enabled: true
                            },
							onClickEvent: function () {
								change_field_value_on_selection('file_tag');
							},
							onSelectItemEvent: function () {
								change_field_value_on_selection('file_tag', 'onSelectItemEvent');
							},
							onChooseEvent: function () {
							    change_field_value_on_selection('file_tag');
							}
                        },
                        adjustWidth: false,
                    });


					function change_field_value_on_selection (field_id, event_type = '') {

						let selected_value = $(`#${field_id}`).getSelectedItemData();

						if (event_type == 'onSelectItemEvent') {
							$(`#${field_id}`).val(selected_value);
						}
						else {
							$(`#${field_id}`).val(selected_value).trigger('change');
						}

					}

					function extract_country_cities (event_type = '') {


						let country = $("#country").getSelectedItemData();

						if (event_type == 'onSelectItemEvent') {
							$('#country').val(country);
						}
						else {
							$('#country').val(country).trigger('change');
						}


						let country_cities_list = org_cities_list.filter(function (value) {

							return value['country'] == country;

						});

						console.log('cities list');
						console.log(country_cities_list);

						let city_options = {
							data: country_cities_list.filter((value, index, self) => self.indexOf(value) === index),
							getValue: "name",
							adjustWidth: false,
							list: {
								maxNumberOfElements: org_cities_list.length,
								hideOnEmptyPhrase: false,
								match: {
									enabled: true
								},
								onClickEvent: function () {
									let city = $("#city").getSelectedItemData();
									console.log('changed city onClickEvent ' + city)
									$('#city').val(city.name).trigger('change');

								},
								onSelectItemEvent: function () {
									let city = $("#city").getSelectedItemData();
									console.log('changed city onSelectItemEvent ' + city)
									$('#city').val(city.name);
								},
								onChooseEvent: function () {
									let city = $("#city").getSelectedItemData();
									console.log('changed country onChooseEvent ' + city)
									$('#city').val(city.name).trigger('change');
								}

							}
						};

						$("#city").easyAutocomplete(city_options);

					}

                    let country_options = {
                        data: org_countries_list.filter((value, index, self) => self.indexOf(value) === index),
//                        getValue: "name",
                        adjustWidth: false,
                        list: {
                            maxNumberOfElements: org_countries_list.length,
							hideOnEmptyPhrase: false,
                            match: {
                                enabled: true
                            },
							onClickEvent: function () {
								extract_country_cities();
							},
							onSelectItemEvent: function () {
								extract_country_cities('onSelectItemEvent');
							},
							onChooseEvent: function () {
								extract_country_cities();
							}
                        }

                    };

                    $("#country").easyAutocomplete(country_options);


					// Previous city block start

					let city_options = {
						data: org_cities_list.filter((value, index, self) => self.indexOf(value) === index),
						getValue: "name",
						adjustWidth: false,
						list: {
							maxNumberOfElements: org_cities_list.length,
							hideOnEmptyPhrase: false,
							match: {
								enabled: true
							},
							onClickEvent: function () {
								let city = $("#city").getSelectedItemData();
								console.log('changed city onClickEvent ' + city);
								$('#city').val(city.name).trigger('change');
							},
							onSelectItemEvent: function () {
								let city = $("#city").getSelectedItemData();
								console.log('changed city onSelectItemEvent ' + city);
								$('#city').val(city.name);
							},
							onChooseEvent: function () {
								let city = $("#city").getSelectedItemData();
								console.log('changed country onChooseEvent ' + city);
								$('#city').val(city.name).trigger('change');
							}
						}
					};

					$("#city").easyAutocomplete(city_options);

					// Previous city block end

                    swiper_instance = swiper_profiles_img(); // get swiper instance for later on use
                    $('.aw_section_results').show();
                    $('.aw_wrapper').preloader('remove');
                    $('#search_resut_count').text(total_results + ' results found for ' + '"' + search_obj['search_str'] + '"');

					if ('view_saved_search' in data && data['view_saved_search'] == true) {
						$.each(data.filter_weights, function (filter_field, filter_weight) {
							$(`#${filter_field}`).bootstrapSlider('enable').bootstrapSlider('setValue', filter_weight);
						});
					}
					
					highlight_selected(common_elements_among_search_results);
					
                }
                else {
                    $('.aw_section_results').hide();
                    $('.aw_wrapper').preloader('remove');
                    var html = '<div class="not-found-results"><div class="not-found-placeholder">No result found</div></div>';
                    $('main#aw_main > .container').append(html);
                }

                first_search_after_pageload = false;
            },
            error: function (resp) {
                console.log(resp);
            }

        });
    }
    window.execute_search = execute_search;
    $(document).on('click', '.search-submit', function (e) {
		if (e.type == 'click' || e.which == 13) {

            e.preventDefault();
			perform_new_search();
					
		}
    });
    $(document).on('keypress', '#search-text', function (e) {
		if (e.which == 13) {
            e.preventDefault();
			perform_new_search();
		}		
    });


    var filters = {};
    var filter_groups = {};  // store filter values group wise
    var save_filter = {};

    $('.aw_range_slider').each(function () {

        let rangeInput = $(this).children('input');

        let rangeMin = -5;
        let rangeMax = 5;
        let rangeAvg = (rangeMin + rangeMax) / 2;
        let rangeSettings = {
            min: rangeMin,
            max: rangeMax,
            tooltip: 'hide',
            value: rangeAvg,
            step: 1,
            enabled: false,
            handle: 'round',
            natural_arrow_keys: true,
            //            formatter: function (value) {
            //                return value;
            //            }
        }

        rangeInput.bootstrapSlider(rangeSettings);

        rangeInput.on('slideStop', function () {
            console.log(rangeInput.bootstrapSlider('getValue'));

            if (!("filter_weights" in search_obj)) {
                search_obj['filter_weights'] = {};
            }

            let name = $(this).attr('id');
            let val = $(this).val();

            if (val != 0) {
                search_obj['filter_weights'][name] = val;
            }
            else {
                delete search_obj['filter_weights'][name];
            }
            console.log(search_obj);

            search();

        })

    });


    function change_filter_status(filter_value, filter_weight_id) {

        let status = 'enable';
        console.log(filter_value);
        console.log(filter_weight_id);
        if (filter_value.trim() == '') {
            status = 'disable';
            $(`#${filter_weight_id}_weightage`).bootstrapSlider('setValue', 0);
        }
        $(`#${filter_weight_id}_weightage`).bootstrapSlider(status);

    }

    var first_time_handler_lock = {
        'country': true,
        'city': true,
//        'area': true,
        'job_title': true,
        'organization_name': true,
        'industry': true,
        'school_name': true
    }

    $('.filter').change(function (e) {

//        console.log(e.type);

        if ($(this).hasClass('suggestion')) {

            let filter_id = $(this).attr('id');
            let value;

//            if ($(this).hasOwnProperty('getSelectedItemData')) {
            if (typeof $(this).getSelectedItemData === 'function') {
                if ((filter_id == 'city' || filter_id == 'country')) {
                    value = $(this).getSelectedItemData().name;
                }
                else {
                    value = $(this).getSelectedItemData();
                }

                console.log("selc");
                console.log($(this).getSelectedItemData());

            }

//            if (typeof value !== 'undefined' && $(this).val().trim() != '' && value != -1 && first_time_handler_lock[filter_id] == true) {
            if (typeof value !== 'undefined' && $(this).val().trim() != '' && value != -1) {

                console.log('User input value ' + $(this).val());
                console.log('Selected value ' + value);

                console.log('first_time_handler_triggered');

                //first_time_handler_lock[filter_id] = false;

                if ($(this).val() != value) {

                    $(this).val(value).trigger('change');

                    if (filter_id == 'country') {

                         get_cities_list(value);

                    }

                    return false;
                }

            }

        }

        if (!("filters" in search_obj)) {
            search_obj['filters'] = {};
        }


        let filter_group = $(this).attr('group');
        let filter_value;
        if (typeof value !== 'undefined') {
            filter_value = value;
            $(this).val(filter_value);
        }
        else {
            filter_value = $(this).val();

        }

        change_filter_status(filter_value, $(this).attr('id'));

        if ($(this).attr('type') == 'checkbox') {

            if ($(this).prop('checked')) {
                $(this).val('on');
                console.log('checked');
            }
            else {
                $(this).val('');
                console.log('unchecked');
            }

        }

        $(`input[group="${filter_group}"]`).each(function () {

            filter_groups[filter_group] = [];

            let name = $(this).attr('name');
            let val = $(this).val();

            if (name && val.trim()) {

				// file tag exception

                search_obj['filters'][name] = val;

                field_placeholders[name] = $(`input[name="${name}"]`).attr('placeholder');

                /*
                <li filter-name="city">
                    <span>City <b>Chicago</b> <i class="fas fa-times"></i></span>
                </li>
                */

            }
            else {
                delete search_obj['filters'][$(this).attr('name')];
            }

        });

        let filters_li = '';

        for (let filter_key in search_obj['filters']) {

            let placeholder = field_placeholders[filter_key];

			let selected_filter_display_value = search_obj['filters'][filter_key];

			/* 			
			if (filter_key == 'file_tag' && selected_filter_display_value == 'no__csv__tags__') {

				selected_filter_display_value = 'No File Tags Selected';

			} 
			*/

            filters_li += `<li filter-name="${filter_key}"><span>${placeholder} <b>${selected_filter_display_value}</b> <i class="fas fa-times"></i></span></li>`;

        }


        $('#applied-filters-ul').html(filters_li);

        search();

    });


    $(document).on('click', '.fa-times', function () {

        let removed_filter = $(this).closest('li');
        let filter_name = removed_filter.attr('filter-name');

        search_obj = search_obj;

        $(`#${filter_name}`).val('');
        console.log('filter name ' + filter_name);
        $(`#${filter_name}_weightage`).bootstrapSlider('setValue', 0).bootstrapSlider('disable');

        if (filter_name == 'member_of_platform' || filter_name == 'degree_of_connection') {

            let btn_filters_class;

            if (filter_name == 'member_of_platform') {
                btn_filters_class = 'mem-of-plat';
            }
            else if (filter_name == 'degree_of_connection') {
                btn_filters_class = 'deg-of-conn';
            }

            $(`.${btn_filters_class}`).each(function () {
                $(this).removeClass('active');
            });

        }



        delete search_obj['filters'][filter_name];

        removed_filter.remove();

        search();

        //console.log(search_obj['filters']);

    });

    function result_card(result_obj, firsDegreeContacts, secondDegreeContacts, thirdDegreeContacts, search_feedback) {

        let result_photo = empty_if_invalid_val(result_obj.photo);
        let result_full_name = empty_if_invalid_val(result_obj.full_name);
        let result_location = concat_loc(result_obj.city, result_obj.country);
        let result_job_location = concat_loc(result_obj.organization_city_1, result_obj.organization_country_1);
        let result_organization_title = empty_if_invalid_val(result_obj.organization_title_1);
        let current_organization = empty_if_invalid_val(result_obj.organization_1);
		let result_school  = empty_if_invalid_val(result_obj.school_1);
        let sec_source_link = empty_if_invalid_val(result_obj.sec_source_link);
        let sec_link_html = '';
		let result_degree_of_connection = '';
		
		if (firsDegreeContacts.indexOf(result_obj.contact_id) > -1) {
			
			result_degree_of_connection = '1st';
			
		}
		else if (secondDegreeContacts.indexOf(result_obj.contact_id) > -1) {
			
			result_degree_of_connection = '2nd';
			
		}
		else if (thirdDegreeContacts.indexOf(result_obj.contact_id) > -1) {
			
			result_degree_of_connection = '3rd';
					
		}
		else {
			
			result_degree_of_connection = 'Out of Network';
			
		}

        // result_degree_of_connection = '1st';
		
        //'<li class="sec"><a href="#"></a></li>'+
        let source_icons = '';

        //        if (sec_source_link != '') {
        //            source_icons += `<span class="aw_card_source_icon"><a href="${sec_source_link}" target="_blank"><img src="/static/img/logos/sec.png" alt="U.S. Securities and Exchange Commission" /></a></span>`;
        //        }

//        let ico_count = 1;
//        while (result_obj['social_profile_link_' + ico_count]) {
//            let platform_source_link = result_obj['social_profile_link_' + ico_count];
//            let platform_icon = result_obj['platform_' + ico_count];
////            console.log(result_obj['social_profile_link_' + ico_count]);
//            source_icons += `<span class="aw_card_source_icon">
//                             <a href="${platform_source_link}" target="_blank">
//                             <img src="/static/img/logos/${platform_icon}.png" alt="U.S. Securities and Exchange Commission" />
//                             </a>
//                             </span>`;
//            ico_count++;
//        }

        let listed_platforms = [];
        let ico_count = 1;
        //while (result_obj['job_profile_link_' + ico_count]) {
		while (ico_count <= result_obj['org_job_to_from_count']) {

            if (listed_platforms.indexOf(result_obj['job_platform_' + ico_count]) == -1) {
//                console.log(result_obj['full_name']);
//                console.log(result_obj['platform_' + ico_count]);
                listed_platforms.push(result_obj['job_platform_' + ico_count]);
                let platform_source_link = result_obj['job_profile_link_' + ico_count];
                let platform_icon = result_obj['job_platform_' + ico_count];

				if (result_obj['job_platform_' + ico_count]) {

					//if (['sec', 'yahoo', 'bloomberg'].indexOf(result_obj['job_platform_' + ico_count].toLowerCase()) < 0)
					if (result_obj['job_platform_' + ico_count].toLowerCase() == 'csv' || result_obj['job_platform_' + ico_count].toLowerCase() == 'null') {
						ico_count++;
						continue;
					}

				}

				if (platform_source_link) {
				    source_icons += `<span class="aw_card_source_icon"><a href="${platform_source_link}" target="_blank"><img src="/static/img/logos/${platform_icon}.png" alt="Social Icon" /></a></span>`;
				}
//				else{
//				    console.log(platform_source_link);
//				    source_icons += `<span class="aw_card_source_icon"><a href="${platform_source_link}" target="_blank"><img src="/static/img/logos/${platform_icon}.png" alt="Social Icon" /></a></span>`;
//				}

//                source_icons += `<span class="aw_card_source_icon"><a href="${platform_source_link}" target="_blank"><img src="/static/img/logos/${platform_icon}.png" alt="Social Icon" /></a></span>`;
            }
            ico_count++;

        }

        let selected = '';

        let feedback_value = {
            '1': '',
            '2': '',
            '3': ''
        };

        let contact_index = -1;

        if (search_feedback.length > 0) {
            if ((contact_index = search_feedback.findIndex(contact_feeback => contact_feeback.contact == result_obj.contact_id)) > -1) {
                feedback_value[search_feedback[contact_index]['feedback']] = 'selected';
            }
        }
		
		let contact_type_head = '';
		let contact_type_head_class = '';

		if (source_icons == '') {
			
			contact_type_head = 'User Imported Contact';
			contact_type_head_class = 'imported_contact_card_head';
			
		}
		else {
			
			contact_type_head = 'Auto Scrapped Contact';
			contact_type_head_class = 'scrapped_contact_card_head';
		
		}
		
		let contact_type_html = '';

		if (user_isa) {
		    contact_type_html = `<div class="${contact_type_head_class}">${contact_type_head}</div>`;
		}

		let confidence_score = result_obj['confidence_score']['calculated_score'];
		console.log('confidence score ');
		console.log(confidence_score);
						
        var html = `<div class="col-md-6">
            <article class="aw_card">
				${contact_type_html}
                <div class="aw_card_body aw_slide_to_click">
                    <div class="aw_card_thumb">
                        <figure><div><img src="${result_photo}" alt=""></div></figure>
                    </div>
                    <div class="aw_card_header">
                        <h3 class="aw_card_title">${result_full_name}</h3>
						<div class="aw_card_degree_of_connection">${result_degree_of_connection}</div>
                        <div class="aw_card_location">${result_job_location}</div>
                        <div class="aw_card_subtitle">${result_organization_title}</div>
                        <div class="aw_card_meta aw_card_org">${current_organization}</div>
						<div class="aw_card_meta aw_card_edu">${result_school}</div>	
						<div class="aw_card_meta aw_card_edu">${confidence_score}% confidence score</div>	
                    </div>
                </div>
				<div class="aw_card_footer">
					<div class="aw_card_likes">
                    <a class="aw_thumbs_up ${feedback_value['1']}" href="javascript:void(0)" data-contact_id="${result_obj.contact_id}">
                        <i class="far fa-thumbs-up"></i>
                    </a>
                    <a class="aw_thumbs_down ${feedback_value['2']}" href="javascript:void(0)" data-contact_id="${result_obj.contact_id}">
                        <i class="far fa-thumbs-down"></i>
                    </a>
                    <a class="aw_thumbs_maybe ${feedback_value['3']}" href="javascript:void(0)" data-contact_id="${result_obj.contact_id}">
                        <i class="far fa-thumbs-up"></i>
                    </a>
					</div>
                    <div class="aw_card_socials">
                        ${source_icons}
					</div>
				</div>
			</article>
		</div>`;

        return html;
    }

    function swiper_slider(data, firsDegreeContacts, secondDegreeContacts, thirdDegreeContacts, response) {
        var company = '';
        var job_title = '';
        var location = concat_loc(data['city'], data['country']);

        if (data.hasOwnProperty('organization_1')) {
            company = empty_if_invalid_val(data['organization_1']);
            job_title = empty_if_invalid_val(data['organization_title_1']);
        }

        let reasons_content = get_search_reason(data);
		//let warmth_of_relationship = '';
        let warmth_of_relationship = get_warmth_of_relationship(data);
        var first_degree_relation = {};
        var second_degree_relation = {};
        var third_degree_relation = {};
        var degree_relation = '';
        var degree_contact_id = data['contact_id'];
		var mutual_connections_list = [];
		var mutual_connections_html_string = '';
		var mutual_connections_img_list = '';
		var common_elements_html_string = '';
		var mutual_connections_names_html_string = '';
		var third_and_third_plus_connections = '';

		first_degree_relation = firsDegreeContacts;
        second_degree_relation = secondDegreeContacts;
        third_degree_relation = thirdDegreeContacts;
		
		let is_scrapped_content = true;
		

        if (first_degree_relation) {
            var containsFirstDegree = (first_degree_relation.indexOf(degree_contact_id) > -1);

        }
        if (second_degree_relation) {
            var containsSecondDegree = (second_degree_relation.indexOf(degree_contact_id) > -1);

			let common_features_org_count = data['common_features']['organization'].length;
			let common_features_edu_count = data['common_features']['education'].length;
			let common_features_names = '';

			if ((common_features_org_count > 0) || (common_features_edu_count > 0)) {
				
				for (let cfio = 0; cfio < common_features_org_count; cfio++) {
					common_features_names +=  `<div>${data['common_features']['organization'][cfio]}</div>`;
				}

				for (let cfie = 0; cfie < common_features_org_count; cfie++) {
					common_features_names +=  `<div>${data['common_features']['education'][cfie]}</div>`;
				}

				if (common_features_names.trim() != '') {
					common_elements_html_string = `<div class="common_features"><h6>Both you and ${data['full_name']} have following in common</h6>${common_features_names}</div>`;			
				}
				
			}

			if (!containsFirstDegree && containsSecondDegree && degree_contact_id in response.mutual_connections) {

				for (let fdci = 0; fdci < response.mutual_connections[degree_contact_id].length; fdci++) {

					mutual_connections_list.push({'name': response.first_degree_connections_details[response.mutual_connections[degree_contact_id][fdci]]['full_name'], 'photo': data['photo']});

				}

				let number_of_mutual_connections = mutual_connections_list.length;

				if (number_of_mutual_connections > 0) {					
					
					let mutual_connections_names = '';
					let mutual_connections_images = '';
					
					for (let mii = 0; mii < number_of_mutual_connections; mii++) {

						let img_src = '/static/img/avatar.png';

						if (mutual_connections_list[mii]['photo'] != '' && mutual_connections_list[mii]['photo'] != 'null' && mutual_connections_list[mii]['photo'] != null && mutual_connections_list[mii]['photo'] !== undefined  && mutual_connections_list[mii]['photo'] !== 'undefined') {
							img_src = mutual_connections_list[mii]['photo'];
						}

						let name_separator = ',';

						if (mii == number_of_mutual_connections - 1) {
							name_separator = ' and';
						}

						mutual_connections_names += `${name_separator} ${mutual_connections_list[mii]['name']}`;
						mutual_connections_images += '<img src="'+img_src+'" />';
					}

					mutual_connections_names_html_string = `<div class="mutual_connection_detail"><h6>${mutual_connections_list.length} mutual connection(s)</h6><div>You ${mutual_connections_names} know ${data['full_name']}</div></div>`;


					mutual_connections_img_list = `<figure class="mutual_connections_thumb">${mutual_connections_images}</figure>`;				

					mutual_connections_html_string = `<div class="aw_mutual_connections">
														${mutual_connections_img_list}
														<div class="mutual_connections">
															${mutual_connections_names_html_string}
														</div>
													  </div>`;

					
				}

			}

        }
        
		if (third_degree_relation) {
            
			var containsThirdDegree = (third_degree_relation.indexOf(degree_contact_id) > -1);

        }

        if(containsFirstDegree == true){
            degree_relation = `<span class="contact-degree-relation">1st</span>`;
        }
        else if (containsSecondDegree == true ) {
            degree_relation = `<span class="contact-degree-relation">2nd</span>`;
        }
        else if (containsThirdDegree == true ) {
            degree_relation = `<span class="contact-degree-relation">3rd</span>`;
			
			if (data['contact_id'] in response.connection_graph) {

				remote_response_graph = response.connection_graph;

				console.log('sec_degree_connection_details');

				if ('sec_degree_connection_details' in response) {

					console.log(response.sec_degree_connection_details);

					remote_sec_deg_connection_details = response.sec_degree_connection_details;

				}

				let first_deg_connections = [];			
				let sec_deg_connections = [];
				
				let cgraph =  response.connection_graph[data['contact_id']];

				for (let degc = 0; degc < cgraph.length; degc++) {
									
					if (first_deg_connections.indexOf(cgraph[degc][1]) === -1) {
						first_deg_connections.push(cgraph[degc][1]);
					}
					
					if (sec_deg_connections.indexOf(cgraph[degc][2]) === -1) {
						sec_deg_connections.push(cgraph[degc][2]);												
					}
					
					third_and_third_plus_connections = `<div class="mutual_connection_detail sec_degree_connection_head"><h6>2nd degree Mutual Connection(s)</h6><a class="third-degree-mut" href="javascript:void(0)" contact-id="${data['contact_id']}"><em>See Connections</em></a>`;
					
				}
				
				console.log(data['contact_id'] + ' in graph found ');
				console.log('Response Graph ' , response.connection_graph[data['contact_id']]);
							
			}			
			
        }
        else {
            degree_relation = `<span class="contact-degree-relation">Out of Network</span>`;	
        }



        let description = '';
        if (data.hasOwnProperty("description") && data['description']) {
            description = empty_if_invalid_val(data['description']);
            description = `<div class='aw_card_meta'>${description}</div>`;
        }

        function* gen_des_content(data){

            let counter = 1;
            let des_counter;
            let profile_html = '';
            let listed_des = [];
            function des_not_shown(des_obj) {
                for (let des_index = 0; des_index < listed_des.length; des_index++) {
                    if (des_obj['des'] == listed_des[des_index]['des'] && des_obj['link'] == listed_des[des_index]['link'] && des_obj['platform'] == listed_des[des_index]['platform']) {
                        return false;
                    }
                }
                return true;
            }
            while ('contact_description_' + counter in data && counter <= 20) {
                let des_info_ = '';
                let des = empty_if_invalid_val(data['contact_description_' + counter]);
                let link = empty_if_invalid_val(data['des_profile_link_' + counter]);
                let platform = empty_if_invalid_val(data['des_platform_' + counter]);
                let des_counter = empty_if_invalid_val(data['contact_description_' + counter]);
                let des_info = { 'des': des_counter, 'des': des, 'link': link, 'platform': platform };

                var highlighted_des = data['highlights']['description'];
//                console.log('highlighted Des' + highlighted_des);


                if (des_not_shown(des_info)) {
                    listed_des.push(des_info);
//                   if (typeof highlighted_des !== 'undefined'){
//                        des = highlighted_des;
//
//                    }
                    // const capitalizeFirstLetter = ([ first, ...rest ], locale = navigator.language) =>
                    //         first.toLocaleUpperCase(locale) + rest.join('')
                    var shortDescription = jQuery.trim(des).substring(0, 200)
                    .split(" ").slice(0, -1).join(" ") + ".....";

					let img_src;
					if (link != '' && platform.toLowerCase() != 'csv') {
					    img_src = '<img src="/static/img/logos/'+platform+'.png" />';
					}
					else {
					    img_src = '';
					}


                    if (des != '' && link != '' ){
                        des_info_ +=    `<div class="aw_source">
                                         <div class="aw_source_box">
                                         <a href="${link}" target="_blank" class="aw_source_link" alt="${platform}">
                                         <div class="aw_source_icon" title="${(platform)}">
                                         ${img_src}
                                         </div>
                                         <div class="aw_source_item">
                                         <div class="aw_card_meta">${shortDescription}</div>
                                         </div>
                                         </a>
                                         </div>
                                         </div>`;
                    }
                }
                counter++;
                yield profile_html + des_info_;
            }
        }

        function* gen_exp_content(data) {
            let counter = 1;
            let org_counter;
            let profile_html = '';
            let listed_experience = [];

            function experience_not_shown(exp_obj) {
                for (let exp_index = 0; exp_index < listed_experience.length; exp_index++) {
                    if (exp_obj['org'] == listed_experience[exp_index]['org'] && exp_obj['org_title'] == listed_experience[exp_index]['org_title'] && exp_obj['org_start'] == listed_experience[exp_index]['org_start'] && exp_obj['org_end'] == listed_experience[exp_index]['org_end'] && exp_obj['link'] == listed_experience[exp_index]['link'] && exp_obj['platform'] == listed_experience[exp_index]['platform']) {
                        return false;
                    }
                }
                return true;
            }

            while ('organization_' + counter in data && counter <= 20) {
                let exp_info_ = '';
                let org_title = empty_if_invalid_val(data['organization_title_' + counter]);
                let org_start = empty_if_invalid_val(data['organization_start_' + counter]);
                let org_end = empty_if_invalid_val(data['organization_end_' + counter]);
                let org_city = empty_if_invalid_val(data['organization_city_' + counter]);
                let org_country = empty_if_invalid_val(data['organization_country_' + counter]);

                let org_location = '';
                if (org_city != '' && org_country != '') {
                    org_location = org_city, ', ' + org_country;
                }
                else if (org_city != '') {
                    org_location = org_city;
                }
                else if (org_country != '') {
                    org_location = org_country;
                }


                let link = empty_if_invalid_val(data['job_profile_link_' + counter]);
                let platform = empty_if_invalid_val(data['job_platform_' + counter]);
                let org_counter = empty_if_invalid_val(data['organization_' + counter]); // name of organization
                
				let job_info = {'org': org_counter, 'org_title': org_title, 'org_start': org_start, 'org_end': org_end, 'link': link, 'platform': platform };

				if (org_counter != '') {
					
					if (org_counter in common_elements_among_search_results['job']) {
						common_elements_among_search_results['job'][org_counter] += 1;
																								
						if (common_elements_among_search_results['job'][org_counter] > common_elements_among_search_results['job']['__max__']['count']) {
							common_elements_among_search_results['job']['__max__'] = {'org': org_counter, 'count': common_elements_among_search_results['job'][org_counter]};																
						}
					}
					else {
						common_elements_among_search_results['job'][org_counter] = 1;
					}
					
					console.log('common_elements_among_search_results ', common_elements_among_search_results);
							
				}

			                				
				if (experience_not_shown(job_info)) {

                    listed_experience.push(job_info);
                    var job_date = '';
                    if (org_start != '' || org_end != '') {
                        var job_date= `<div class='aw_card_meta'>(${org_start} - ${org_end})</div>`;
                    }
					// const capitalizeFirstLetter = ([ first, ...rest ], locale = navigator.language) =>
					// 	first.toLocaleUpperCase(locale) + rest.join('')

					let img_src;
					if (link != '' && platform.toLowerCase() != 'csv') {
					    img_src = '<img src="/static/img/logos/'+platform+'.png" />';
					}
					else if (platform.toLowerCase() == 'csv') {
					    img_src = '<img src="/static/img/logos/'+platform.toLowerCase()+'.png" />';
					}
					else {
					    img_src = '';
					}

                    if (org_title != ''){

                        exp_info_ += ` <div class="aw_source_box">
                                    <a href="${link}" target="_blank" class="aw_source_link" alt="${platform}">
                                    <div class="aw_source_icon" title="${(platform)}">
                                    ${img_src}
                                    </div>
                                    <div class="aw_source_item">
                                    <div class="aw_card_subtitle">${org_title}</div>
                                    <div class="aw_card_meta">${org_location}</div>
                                    <div class="aw_card_meta">${job_date}</div>
                                    <div class="aw_card_meta">${org_counter}</div>
                                    </div>
                                    </a>
                                    </div>`;
                    }
                }
                counter++;
                yield profile_html + exp_info_;
            }
        }

        function* gen_edu_content(data) {
            let counter = 1;
            let org_counter;
            let profile_html = '';
            let listed_education = [];

            function education_not_shown(edu_obj) {
                for (let edu_index = 0; edu_index < listed_education.length; edu_index++) {
                    if (edu_obj['edu_degree'] == listed_education[edu_index]['edu_degree'] && edu_obj['edu_school'] == listed_education[edu_index]['edu_school'] && edu_obj['edu_start'] == listed_education[edu_index]['edu_start'] && edu_obj['edu_end'] == listed_education[edu_index]['edu_end'] && edu_obj['link'] == listed_education[edu_index]['link'] && edu_obj['platform'] == listed_education[edu_index]['platform']) {
                        return false;
                    }
                }
                return true;
            }

            while ('school_' + counter in data && counter <= 20) {
                let edu_info_ = '';
                let edu_school = empty_if_invalid_val(data['school_' + counter]);
                let edu_start = empty_if_invalid_val(data['school_start_' + counter]);
                let edu_end = empty_if_invalid_val(data['school_end_' + counter]);
                let link = empty_if_invalid_val(data['scool_profile_link_' + counter]);
                let platform = empty_if_invalid_val(data['school_platform_' + counter]);
                let edu_degree = empty_if_invalid_val(data['degree_' + counter]);

                let edu_info = {'edu_degree': edu_degree, 'edu_school': edu_school, 'edu_start': edu_start, 'edu_end': edu_end, 'link': link, 'platform': platform };

				if (edu_school != '') {
					
					if (edu_school in common_elements_among_search_results['edu']) {
						common_elements_among_search_results['edu'][edu_school] += 1;

						if (common_elements_among_search_results['edu'][edu_school] > common_elements_among_search_results['edu']['__max__']['count']) {
							common_elements_among_search_results['edu']['__max__'] = {'edu': edu_school, 'count': common_elements_among_search_results['edu'][edu_school]};																
						}					
						
					}
					else {
						common_elements_among_search_results['edu'][edu_school] = 1;
					}
										
					console.log('common_elements_among_search_results ... ', common_elements_among_search_results);
												
				}

		
                if (education_not_shown(edu_info)) {
                    listed_education.push(edu_info);
					
                    var edu_date = '';
                    if (edu_start != '' || edu_end != '') {
                        var edu_date= `<div class='aw_card_meta'>(${edu_start} - ${edu_end})</div>`;
                    }
                    // const capitalizeFirstLetter = ([ first, ...rest ], locale = navigator.language) =>
                    //         first.toLocaleUpperCase(locale) + rest.join('')

					let img_src;
					if (link != '' && platform.toLowerCase() != 'csv') {
					    img_src = '<img src="/static/img/logos/'+platform+'.png" />';
					}
					else if (platform.toLowerCase() == 'csv') {
					    img_src = '<img src="/static/img/logos/'+platform.toLowerCase()+'.png" />';
					}
					else {
					    img_src = '';
					}


                    if (edu_school != '') {
                        edu_info_ += ` <div class="aw_source_box">
                                    <a href="${link}" target="_blank" class="aw_source_link" alt="${platform}">
                                    <div class="aw_source_icon" title="${(platform)}">
                                    ${img_src}
                                    </div>
                                    <div class="aw_source_item">
                                    <div class="aw_card_subtitle">${edu_school}</div>
                                    <div class="aw_card_meta">${edu_date}</div>
                                    <div class="aw_card_meta">${edu_degree}</div>
                                    </div>
                                    </a>
                                    </div>`;
                    }
                }
                counter++;
                yield profile_html + edu_info_;
            }
        }


        var expereince_string = '';
        var exp_body = '';
        var edu_body = '';
        var des_body = '';
        var reason = '';

        for (const des_info of gen_des_content(data)) {
            des_body += des_info;
        }

        for (const exp_info of gen_exp_content(data)) {
            exp_body += exp_info;
        }

        for (const edu_info of gen_edu_content(data)) {
            edu_body += edu_info;
        }

        let full_name = empty_if_invalid_val(data['full_name']);
        let sec_source_link = empty_if_invalid_val(data['sec_source_link']);
        let industry = empty_if_invalid_val(data['industry']);

        var profile_content = '';
        if (des_body != ''){
            profile_content = `<div class="aw_source_holder">
                               <h6 class="aw_source_title">Profile</h6>
                                ${des_body}
                                </div>`;
        }

        var job_title_content = '';
        if (exp_body != ''){
            job_title_content = `<div class="aw_source_holder">
                                 <h6 class="aw_source_title">Job Title</h6>
                                 <div class="aw_source">
                                 ${exp_body}
                                 </div>
                                 </div> `;
        }

        var education_content = '';
        if (edu_body != ''){
            education_content = `<div class="aw_source_holder">
                                 <h6 class="aw_source_title">Education</h6>
                                 <div class="aw_source">
                                 ${edu_body}
                                 </div>
                                 </div> `;
        }

        var article_counter = 0;
		
		let twitter_tweets = '';
		let twitter_notification = '';
		
		function gen_twitter_notification (data) {

			let tweet_notification = '';
			
			if ('twitter_tweets' in data && data['twitter_tweets'].length > 0) {
				
				tweet_notification += `<div class="aw_card_body">`;
				tweet_notification += `<div class="tweet_notification_container"><a href="javascript:void(0)" contact-id="${data['contact_id']}" class="tweet_notification_link">${data['twitter_tweets'].length} matching tweets</a></div>`;									
				tweet_notification += `</div>`;
														
			}
			
			return tweet_notification;
			
		}
		
		function gen_tweet_content (data) {
			
			let tweet_content = ''
			
			if ('twitter_tweets' in data && data['twitter_tweets'].length > 0) {
				
				tweet_content += `<div id="tp-tweets-${data['contact_id']}" class="aw_card_body tp_detail_tweets">`;
				//tweet_content += `<h6>Contact Tweets</h6>`;	
				
				for (let tci = 0; tci < data['twitter_tweets'].length; tci++) {
				
					//tweet_content += `<div class="tweet_content tweet_content_container"><a href="https://twitter.com/${data['twitter_profile']}/status/${data['twitter_tweets'][tci]['id']}" target="_blank">${data['twitter_tweets'][tci]['text']}</a></div>`;					
					tweet_content += `<div class="tweet_content tweet_content_container"><a href="https://twitter.com/${data['twitter_profile']}/status/${data['twitter_tweets'][tci]['id']}" target="_blank">${data['twitter_tweets'][tci]['text']}</a></div>`;
					
				}
				
				tweet_content += `</div>`;
														
			}
			
			return tweet_content
			
		}
		
		
		twitter_tweets = gen_tweet_content(data);
		twitter_notification = gen_twitter_notification(data);
        
		var html = '<div class="swiper-slide">' +
            '<article class="aw_card">' +
            '<div class="aw_card_header">' +
            '<div class="aw_card_thumb">' +
            '<figure>' +
            '<a href="javascript:void(0)"><img src="' + data['photo'] + '" alt="' + full_name + '" /></a>' +
            '</figure>' +
            '</div>' +
            '<div class="aw_card_info">' +
            '<h3 class="aw_card_title">' +
            '<a href="javascript:void(0)">' + full_name + '</a> - ' + degree_relation +
            '</h3>' +
            '<div class="aw_card_location_swiper">' + location + '</div>' +
            '<div class="aw_card_subtitle">' + job_title + '</div>' +
            '<div class="aw_card_meta">' + company + '</div>' +
            '<div class="aw_card_meta">' + industry + '</div>' +
            '</div>' +
            '</div>' +
            //'<div class="aw_card_reason"><p>' + reasons_content + '</p></div>' +
			'<div class="aw_card_reason"><p>' + third_and_third_plus_connections + '</p></div>' +
            '<div class="connnections_wrapper">' +
                '<div class="connnections_container">' +
					mutual_connections_html_string +
                '</div>' +
				'<div>' + 
					warmth_of_relationship +
				'</div>' + 
            '</div>' +
			'<div class="aw_card_reason">' + reasons_content + '</div>' +
            '<div class="aw_card_body">' +
                profile_content +
                job_title_content +
                education_content +
            '</div>' +
			twitter_notification + 
			twitter_tweets + 
			'</article>' +
            '</div>';
        $('.swiper-wrapper').append(html);
    }

    function save_viewed_contact (contact_id) {

        $.ajax({
            url: '/search-history/save-viewed-contact',
            data: {'contact_id': contact_id},
            success: function (data) {
//                console.log(data);
            }
        });

    }


    function swiper_profiles_img() {
        var awSwiper = new Swiper('.swiper-container', {
            autoHeight: true,
            observer: true,
            observeParents: true,
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev'
            },
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
                renderBullet: function (index, className) {
                    return `<div class="${className}"><img src="${bulleteImg[index]}" /></div>`;
                },
                dynamicBullets: true,
                dynamicMainBullets: 1
            },
            on: {
                sliderMove: function () {
                    console.log('Slider move');
                }
            }
        });

        return awSwiper;
    }

    $(document).on('click', '.aw_slide_to_click', function () {

        if (swiper_instance !== null) {
            
			var index = $(this).closest('.col-md-6').index();
            swiper_instance.slideTo(index);
			//$("html, body").animate({ scrollTop: 0 }, 'slow'); // bring on top
        
		}

    });

    function get_search_reason (data) {

        let occr_fields_list = data['occurance_fields'];
		let highlights = data['highlights'];
        let common_institutions = data['common_institutions'];
        let reasons_html = '';
        let reason_field_or_value = '';
        let text_found = '';

        // let fields_lists = ['first_name', 'last_name', 'industry', 'organization', 'organization_title_', 'description'];

        //let occr_field_name = Object.keys(occr_fields_list[ofi])[0];
		console.log('Occr field ' , occr_fields_list);
		
        for (let ofi = 0; ofi < occr_fields_list.length; ofi++) {

            let occr_field_name = Object.keys(occr_fields_list[ofi])[0];
			console.log('Occr field name ', occr_field_name);

            if (occr_field_name == 'first_name' || occr_field_name == 'last_name') {
                reason_field_or_value = 'Name';
                text_found = data['highlights'][occr_field_name];
                let name = '';
                if (data['highlights'].hasOwnProperty('first_name') || data['highlights'].hasOwnProperty('last_name') || data['highlights'].hasOwnProperty('full_name')) {
                    name += data['highlights']['full_name'];
                }

				//reasons_html = `<b>Result Reason:</b> <u>${name}</u> in <span class="result_reason_field">Name</span> field`;
				reasons_html = `<h6>Result Reason</h6> <u>${name}</u> in <span class="result_reason_field">Name</span> field`;

            }
            else if (occr_field_name == 'industry') {
                reason_field_or_value = 'Industry';
                text_found = data['highlights'][occr_field_name];

                //reasons_html = `<b>Industry</b> ${data['highlights']['industry']}`;
				reasons_html = `<b>Result Reason</b> <u>${data['highlights']['industry']}</u> in <span class="result_reason_field">Industry</span> field`;

            }
            else if (occr_field_name.indexOf('organization_title_') > -1) {
                reason_field_or_value = 'job ';
                let curr_or_prev = '';
                let job_title = '';
                if (occr_field_name.match(/_(\d+$)/)[0].slice(1) == '1') {
                    curr_or_prev = 'Current';
                    job_title = data['job_title'];
                }
                else {
                    curr_or_prev = 'Past';
                    job_title = occr_fields_list[ofi][occr_field_name];
                }

                //reasons_html = `<b>${curr_or_prev} ${reason_field_or_value}</b> ${job_title}`;
                reasons_html = `<h6>Result Reason</h6>  <b>${curr_or_prev} ${reason_field_or_value}</b> ${job_title} in <span class="result_reason_field">Industry</span> field`;
				
            }
			else if (occr_field_name.indexOf('job_title') > -1) {
				console.log(`Organization title ${occr_field_name}`); 
                reason_field_or_value = 'job ';
                let curr_or_prev = '';
                let job_title = '';
				
				job_title = occr_fields_list[ofi][occr_field_name];


                //reasons_html = `<b>${curr_or_prev} ${reason_field_or_value}</b> ${job_title}`;
                reasons_html = `<h6>Result Reason</h6> <u>${job_title}</u> in <span class="result_reason_field">Job Title</span> field`;
				
			}
            else if (occr_field_name.indexOf('organization_') > -1) {
                reason_field_or_value = data['highlights']['organization_name'];
                let curr_or_prev = '';
                if (occr_field_name.match(/_(\d+$)/)[0].slice(1) == '1') {
                    curr_or_prev = 'Current';
                }
                else {
                    curr_or_prev = 'Past';
                }
                reason_field_or_value = reason_field_or_value;
                text_found = occr_fields_list[ofi][occr_field_name];
                reasons_html = `<h6>Result Reason</h6>${reason_field_or_value} in <span class="result_reason_field">${curr_or_prev} organization</span> field`;
            }
            else if (occr_field_name.indexOf('degree_') > -1) {
                reason_field_or_value = 'degree ';
                let curr_or_prev = '';
                let degree_title = '';
                if (occr_field_name.match(/_(\d+$)/)[0].slice(1) == '1') {
                    curr_or_prev = 'Current';
                    degree_title = data['degree_1'];
                }
                else {
                    curr_or_prev = 'Past';
                    degree_title = occr_fields_list[ofi][occr_field_name];
                }

                reasons_html = `<h6>Result Reason</h6> <b>${curr_or_prev} ${reason_field_or_value}</b> ${degree_title}`;
            }
			else if (occr_field_name.indexOf('degree') > -1) {
                reason_field_or_value = 'Degree ';
				
                let degree_title = occr_fields_list[ofi][occr_field_name];

                reasons_html = `<h6>Result Reason</h6><span class="result_reason_field">${degree_title}</span> in <b>${reason_field_or_value}</b> `;				
			}
            else if (occr_field_name.indexOf('school_') > -1) {
				let school_occr_index = occr_field_name.match(/_(\d+$)/)[0].slice(1);
				let reason_field_or_value = data['school_'+school_occr_index];
				let curr_or_prev = '';
                if (school_occr_index == '1') {
                    curr_or_prev = 'Current';
                }
                else {
                    curr_or_prev = 'Past';
                }
                reason_field_or_value = reason_field_or_value;
                text_found = occr_fields_list[ofi][occr_field_name];
                reasons_html = `<h6>Result Reason</h6> <b>${curr_or_prev} School: </b> ${reason_field_or_value}`;
            }

            break;

        }

        if (occr_fields_list.length === 0) {
			
			if (typeof data['highlights']['full_name'] !== 'undefined') {
                text_found = data['highlights']['full_name'];
                reasons_html = `<h6>Result Reason</h6><div>${text_found} in <span class="result_reason_field">Name</span></div>`;										
			}
            else if (typeof data['highlights']['job_title'] !== 'undefined') {
                text_found = data['highlights']['job_title'];
                reasons_html = `<h6>Result Reason</h6><div>${text_found} in <span class="result_reason_field">Job Title</span></div>`;
            }
            else if (typeof data['highlights']['description'] !== 'undefined') {
                text_found = data['highlights']['description'][0];
                reasons_html = `<h6>Result Reason</h6><div>Matching text found in <span class="result_reason_field">Profile</span> description (See <em>Emphasized</em> text in profile) </div><div class="mt-2"><b>Profile</b> ${text_found}</div>`;
            }
			/*
			else if (typeof data['highlights']['degree'] !== 'undefined') {
				console.log('Matching degree found ');
				text_found = data['highlights']['degree'][0];
                reasons_html = `<h6>Result Reason</h6><div>{text_found} Matching text found in <span class="result_reason_field">Degree</span></div>`;
			}
			*/

        }

        return reasons_html;

    }

    function get_warmth_of_relationship (data) {

        let reasons_html = '';
		
		let num_of_common_institutions = 0;		

        let common_institutions = data['common_institutions'];

        let commonly_attended_institutions_types = Object.keys(common_institutions);
		
		let commonly_attended_institutions_types_len = commonly_attended_institutions_types.length;

        if (commonly_attended_institutions_types_len > 0) {

			num_of_common_institutions += data['common_institutions']['education'].length
			num_of_common_institutions += data['common_institutions']['organization'].length

            reasons_html += `<div class="aw_warmth_relations"><h6>Warmth of Relations</h6>`

			let already_listed_common_institution = [];
			
			if (num_of_common_institutions > 0) {
				
				for (let cai_index = 0; cai_index < commonly_attended_institutions_types_len; cai_index++) {

					if (common_institutions[commonly_attended_institutions_types[cai_index]].length > 0) {

						for (let ci = 0; ci < common_institutions[commonly_attended_institutions_types[cai_index]].length; ci++) {

							if (already_listed_common_institution.indexOf(common_institutions[commonly_attended_institutions_types[cai_index]][ci]) === -1) {

								already_listed_common_institution.push(common_institutions[commonly_attended_institutions_types[cai_index]][ci]);
								reasons_html += `<div>${common_institutions[commonly_attended_institutions_types[cai_index]][ci]}</div>`;
							}

						}

					}

				}				
					
			}
			else {
				
				reasons_html += `<div>None</div>`;
						
			}

            reasons_html += '</div>';

        }

        return reasons_html;

    }



    function empty_if_invalid_val(value) {

        if (typeof value === 'undefined' || value == null || value == 'null' || value == 'NULL') {
            return '';
        }

        return value;

    }

    function concat_loc(city, country) {

        return (empty_if_invalid_val(city) ? city + ', ' + empty_if_invalid_val(country) : empty_if_invalid_val(country));

    }

    var search_like_array = {};

    $(document).on('click', '.aw_card_likes > a', function (e) {
        var thumbs_up, thumbs_down, thumbs_maybe;

        $(this).addClass('selected');
        $(this).siblings().removeClass('selected');

        var contant_id = $(this).attr("data-contact_id");
        var search_key = document.getElementById("search-text").value;
        if ($(this).is('.aw_thumbs_up.selected')) {
            thumbs_up = 1;
        }
        if ($(this).is('.aw_thumbs_down.selected')) {
            thumbs_down = 2;
        }
        if ($(this).is('.aw_thumbs_maybe.selected')) {
            thumbs_maybe = 3;
        }
        search_like_array['search_key'] = search_key;
        search_like_array['contant_id'] = contant_id;
        search_like_array['thumbs_up'] = thumbs_up;
        search_like_array['thumbs_down'] = thumbs_down;
        search_like_array['thumbs_maybe'] = thumbs_maybe;

        $.ajax({
            url: '/search-history/search_like',
            dataType: 'json',
            data: search_like_array,
            success: function (data) {

            },
            error: function (resp) {
                console.log(resp);
            }
        });

        e.preventDefault();
    });

    function get_search_feedback() {

        let search_str = $('#search-text').val();

        let search_feedback = [];

        $.ajax({
            url: '/search-history/search_feedback',
            dataType: 'json',
            data: { 'search_str': search_str },
            async: false,
            success: function (data) {
                search_feedback = data;
            },
            error: function (resp) {
                console.log(resp);
            }
        });

        return search_feedback;

    }

    function get_cities_list (country) {

        function city_change_callback () {
            let city = $("#city").getSelectedItemData().name;
            $('#city').val(city).trigger('change');
        }

        $.ajax({
            url: '/get-cities',
            data: {'country': country.trim()},
            success: function (cities_list) {

                let city_options = {
                    data: cities_list,
                    getValue: "name",
                    listLocation: function (country_states) {
                        let cities_suggestions = [];
                        cities_suggestions = country_states.states.flatMap(state => state.cities);
                        console.log(cities_suggestions);

                        return cities_suggestions;
                    },
                    template: {
                        type: "description",
                        fields: {
                            description: "state"
                        }
                    },
                    list: {
//                        maxNumberOfElements: listLocation.length,
                        match: {
                            enabled: true
                        },
                        onChooseEvent: city_change_callback,
                        onKeyEnterEvent: city_change_callback
                    },
                    adjustWidth: false,
                };

                $("#city").easyAutocomplete(city_options);

            }
        });

    }

    if ($('#country').length) {

        function country_change_callback () {

            let country = $("#country").getSelectedItemData().name;
            get_cities_list(country);
            first_time_handler_lock['city'] = true;
            $('#country').val(country).trigger('change');

        }

    }

    $('.mem-of-plat').click(function () {
        $('#member_of_platform').val($(this).attr('val')).trigger('change');
    });

    $('.deg-of-conn').click(function () {
        $('#degree_of_connection').val($(this).attr('val')).trigger('change');
    });

    if ($("a.search_history")[0]){

        $('a.search_history').each(function () {

            let search_history_filters = $(this).attr('data-filters');
            let search_history_tags = `<div class="search_history_tags">`;

            if (search_history_filters != '' && search_history_filters != null) {

                let parsed_filters = JSON.parse(search_history_filters);

                for (let filter_index in parsed_filters) {

                    if (filter_index == 'country' || filter_index == 'city') {

                        if ('city' in parsed_filters && 'country' in parsed_filters) {
                            search_history_tags += `<span>${parsed_filters['city']}, ${parsed_filters['country']}</span>`;
                            delete parsed_filters['city'];
                            delete parsed_filters['country'];
                        }
                        else {
                            search_history_tags += `<span>${parsed_filters[filter_index]}</span>`;
                        }

                    }
                    else {
                          search_history_tags += `<span>${parsed_filters[filter_index]}</span>`;
                    }

                }

            }

            search_history_tags += `</div>`;
            $(this).find(':nth-child(1)').after(search_history_tags);

        });

    }


    $('body').on("change", ".file-tags-suggestions", function () {

        let checkbox_filetag_index = -1;

        if (file_tags_checkbox_list === '') {
            //file_tags_checkbox_list = file_tags_suggestions_list.slice();
            file_tags_checkbox_list = file_tags_suggestions_list.slice();
			console.log('updated list ');
        }

        console.log('file tag list ');
        console.log(file_tags_checkbox_list);

        let checkbox_filetag_value = $(this).val();

        if (typeof file_tags_checkbox_list == 'object') {
             checkbox_filetag_index = file_tags_checkbox_list.indexOf(checkbox_filetag_value);
        }

        if (checkbox_filetag_value == 'all') {

            if ($(this).prop('checked')) {
                file_tags_checkbox_list = file_tags_suggestions_list.slice();
                $('.file-tags-suggestions').prop('checked', true);
                //$('#file_tag').val(file_tags_checkbox_list.join(','));

                $('#file_tag').val('');
                //delete search_obj['filters']['file_tag'];

            }
            else {
                file_tags_checkbox_list = [];
                $('.file-tags-suggestions').prop('checked', false);
                $('#file_tag').val('no__csv__tags__');
            }


        }
        else {

            if ($(this).prop('checked') === true) {

                if (file_tags_checkbox_list.indexOf(checkbox_filetag_value) === -1) {
                    file_tags_checkbox_list.push(checkbox_filetag_value);
                }

                if (file_tags_checkbox_list.length === file_tags_suggestions_list.length) {
                    $('#all-file-tags').prop('checked', true);
                }

                 //$('#file_tag').val(encodeURI(file_tags_checkbox_list.join(',')));
                $('#file_tag').val((file_tags_checkbox_list.join(',')));

            }
            else {
                $('#all-file-tags').prop('checked', false);
                if (checkbox_filetag_index > -1) {
                     file_tags_checkbox_list.splice(checkbox_filetag_index, 1);

                     console.log('spliced array');
                     console.log(file_tags_checkbox_list);

                     if (file_tags_checkbox_list.length == 0) {
                         //$('#file_tag').val(encodeURI(file_tags_checkbox_list.join(',')));
                         $('#file_tag').val('no__csv__tags__');
                     }
                     else {
                         $('#file_tag').val((file_tags_checkbox_list.join(',')));
                     }


                }

            }

        }

    });

    $('body').on('click', "#apply-file-tag-filter", function () {

            console.log(search_obj['filters']);

            console.log('fle tag value ');
            console.log($('#file_tag').val());

            console.log('file_tags_checkbox_list');
            console.log(file_tags_checkbox_list.join(','));


            $('#file_tag').trigger('change');

    });
	
	$('body').on("click", ".third-degree-mut", function () {
		
		let contact_id = $(this).attr('contact-id');

		console.log('rrg', remote_response_graph);
		console.log('sdcd', remote_sec_deg_connection_details);

		let paths_list = remote_response_graph[contact_id];

		let ul_html = '';	

		$('#modalMutualConnections ul.mdl_mutual_connection_list').html('');

		for (let pl = 0; pl < paths_list.length; pl++) {

			let fdc = paths_list[pl][1];
			let sdc = paths_list[pl][2];

			let fdc_photo = '/static/img/avatar.png';

			if (remote_sec_deg_connection_details[sdc]['photo']) {
				fdc_photo = remote_sec_deg_connection_details[sdc]['photo'];
			}

			let first_degree_connection_names = '';


			let second_degree_paths_list = remote_response_graph[sdc];
			let first_degree_name_separator = '';

			for (let sdpl = 0; sdpl < second_degree_paths_list.length; sdpl++) {

				if (sdpl > 0) {
					if (sdpl == second_degree_paths_list.length - 1) {
						first_degree_name_separator = ` and `;
					}
					else {
						first_degree_name_separator = `, `;
					}
				}	

				let fdcd = second_degree_paths_list[sdpl][1];					
				first_degree_connection_names += `${remote_sec_deg_connection_details[fdcd]['full_name']} `;
				
			}

			let org_job_title = '';

			if (remote_sec_deg_connection_details[sdc]['job_title'] && remote_sec_deg_connection_details[sdc]['organization_name']) {
				org_job_title = `${remote_sec_deg_connection_details[sdc]['job_title']}, ${remote_sec_deg_connection_details[sdc]['organization_name']}`; 
			}
			else if (remote_sec_deg_connection_details[sdc]['organization_name']) {
				org_job_title = `${remote_sec_deg_connection_details[sdc]['organization_name']}`; 
			}
			else if (remote_sec_deg_connection_details[sdc]['job_title']) {
				org_job_title = `${remote_sec_deg_connection_details[sdc]['job_title']}`; 
			}

			ul_html += `<li>
							<figure>
								<img src="${fdc_photo}" />
							</figure>
							<div class="mdl_mutual_conn_item">
								<div class="mdl_conn_title">${remote_sec_deg_connection_details[sdc]['full_name']} (2nd)</div>
								<div class="mdl_conn_detail">${org_job_title}</div>
								<div class="mdl_conn_detail"><span class="sec_fst_deg_con_names">${first_degree_connection_names}${first_degree_name_separator}</div>
							</div>
					    </li>`; 
							
		}

		$('#modalMutualConnections ul.mdl_mutual_connection_list').html(ul_html);

		$('#modalMutualConnections').modal('show');
		
	});
		
	$('body').on("click", ".tweet_notification_link", function () {

		let contact_id = $(this).attr('contact-id');

		//let tp_tweets_html = $(`#tp-tweets-${contact_id}`).html();
		let $tp_tweets_html = $(`#tp-tweets-${contact_id}`).clone().attr('id', `tp-tweets-modal-${contact_id}`).removeClass('tp_detail_tweets');
		
		console.log($tp_tweets_html);
		//console.log(tp_tweets_html);
		
		
		$('#modalPosts .modal-body').html($tp_tweets_html);

		$('#modalPosts').modal('show');

						
	});
	
	function highlight_selected (common_elements_among_search_results) {
		
		let edu_max = common_elements_among_search_results['edu']['__max__']['edu'];
		let job_max = common_elements_among_search_results['job']['__max__']['org'];
		
		$('article div.aw_card_org').each(function () {
						
			if ($(this)[0].outerText == job_max) {
				
				$(this)[0].style.color = '#f95252';
				
			}
						
		});
		
		$('article div.aw_card_edu').each(function () {
			
			if ($(this)[0].outerText == edu_max) {
				
				$(this)[0].style.color = '#f95252';
				
			}
						
		});		
		
	}
	
	
	/* var stickyTop = $('#resultsCarousel').offset().top;
	
 	$(window).scroll(function() {
		
		var windowTop = $(window).scrollTop();
		
		//if (stickyTop < windowTop && $(".seerch-result-holder").height() + $(".seerch-result-holder").offset().top - $("#resultsCarousel").height() > windowTop) {
		
		if (stickyTop < windowTop && windowTop > $('#resultsCarousel').height()) {
		
			$('#resultsCarousel').css('position', 'fixed');
    
		} else {
			
			$('#resultsCarousel').css('position', 'relative');
		
		}
		
	});	 */ 
			
})(jQuery);

function is_str_valid_json (json_str) {
    try {
        var o = JSON.parse(json_str);
        if (o && typeof o === "object") {
            return o;
        }
    }
    catch (e) { }

    return false;
}